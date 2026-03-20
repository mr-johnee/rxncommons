from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Header, Query
from app.core.tasks import process_file_metadata

from sqlalchemy.orm import Session
from app.api import deps

import magic
from app.crud import crud_file, crud_dataset

from app.schemas.file import FileUploadResponse
from app.models.user import User
from app.models.dataset import DatasetFile, FileColumn, Dataset, DatasetVersion
from app.models.storage import PhysicalStorageObject
from app.core.dataset_access import evaluate_dataset_access
from app.core.storage import minio_client, generate_file_key
import hashlib
from uuid import UUID
import os
import tempfile
import pandas as pd
from pydantic import BaseModel, Field
from typing import List, Optional
from fastapi.responses import StreamingResponse
from urllib.parse import quote

router = APIRouter()


class PreviewResponse(BaseModel):
    filename: str
    columns: List[str]
    rows: List[dict]
    preview_type: str
    truncated: bool


class FileColumnUpdate(BaseModel):
    column_name: str
    description: str = Field(..., max_length=500)


class FileMetadataUpdateReq(BaseModel):
    description: Optional[str] = Field(None, max_length=500)
    columns: List[FileColumnUpdate] = []


class FileMetadataResponse(BaseModel):
    file_id: UUID
    description: Optional[str]
    upload_status: str
    row_count: Optional[int]
    error_message: Optional[str]
    columns: List[dict]


def _ensure_dataset_editable(dataset):
    if dataset.dataset_status == 'pending_review':
        raise HTTPException(status_code=409, detail="dataset_under_review_locked")


def _can_view_version_for_dataset(dataset: Dataset, version: DatasetVersion, current_user: User | None) -> bool:
    if version.status == "published":
        return True
    if not current_user:
        return False
    return current_user.role == "admin" or current_user.id == dataset.owner_id


def _ensure_dataset_readable(
    db: Session,
    dataset_id: UUID,
    current_user: User | None,
    dataset_access_token: str | None,
) -> Dataset:
    dataset = crud_dataset.get_dataset(db, dataset_id)
    allowed, password_required = evaluate_dataset_access(
        db=db,
        dataset=dataset,
        current_user=current_user,
        access_token=dataset_access_token,
    )
    if not allowed:
        if password_required:
            raise HTTPException(status_code=403, detail={"code": "dataset_access_password_required"})
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


def _load_preview_rows(tmp_path: str, filename: str, max_rows: int = 50):
    filename_l = filename.lower()
    if filename_l.endswith('.csv'):
        df = pd.read_csv(tmp_path, nrows=max_rows)
        return "table", list(df.columns), df.fillna('').to_dict(orient='records')
    if filename_l.endswith('.xlsx'):
        df = pd.read_excel(tmp_path, nrows=max_rows, engine='openpyxl')
        return "table", list(df.columns), df.fillna('').to_dict(orient='records')
    if filename_l.endswith('.xls'):
        df = pd.read_excel(tmp_path, nrows=max_rows, engine='xlrd')
        return "table", list(df.columns), df.fillna('').to_dict(orient='records')
    if filename_l.endswith('.json'):
        df = pd.read_json(tmp_path)
        if isinstance(df, pd.Series):
            df = df.to_frame(name='value')
        if len(df) > max_rows:
            df = df.head(max_rows)
        return "table", list(df.columns), df.fillna('').to_dict(orient='records')
    if filename_l.endswith('.txt') or filename_l.endswith('.xml'):
        with open(tmp_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = [line.rstrip('\n') for line in f.readlines()[:max_rows]]
        return "text", ["content"], [{"content": line} for line in lines]
    return "text", ["content"], [{"content": "该文件类型暂不支持文本预览，请直接下载查看。"}]

@router.post("", response_model=FileUploadResponse)
def upload_file(
    dataset_id: UUID,
    version_num: int = Form(...),
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    # Verify dataset exists and belongs to user
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this dataset")
    _ensure_dataset_editable(dataset)


    # Verify version exists
    version = crud_file.get_version_by_num(db, dataset_id, version_num)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    if version.status != 'draft':
        raise HTTPException(status_code=409, detail="version_not_editable")

    # Same version cannot contain duplicate filenames.
    existing_same_name = db.query(DatasetFile).filter(
        DatasetFile.version_id == version.id,
        DatasetFile.filename == file.filename
    ).first()
    if existing_same_name:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "duplicate_filename",
                "filename": file.filename,
                "version_num": version_num,
            }
        )

    # Extension whitelist
    # Keep whitelist aligned with metadata pipeline and review requirements.
    allowed_exts = [".csv", ".xlsx", ".xls"]
    filename_lower = file.filename.lower()
    if not any(filename_lower.endswith(ext) for ext in allowed_exts):
        raise HTTPException(status_code=400, detail="only_csv_xlsx_supported")

    # Magic Mime check
    file.file.seek(0)
    head_chunk = file.file.read(2048)
    mime_type = magic.from_buffer(head_chunk, mime=True)
    
    # We do a loose check for common text/excel mimes, or reject if it's executable
    if "executable" in mime_type or "x-sharedlib" in mime_type:
        raise HTTPException(status_code=400, detail="Executable files are forbidden")


    # Read and process file stream, calculate hash
    sha256_hash = hashlib.sha256()
    file.file.seek(0)
    while chunk := file.file.read(8192):
        sha256_hash.update(chunk)
    file_hash = sha256_hash.hexdigest()
    
    file_size = file.file.tell() # Get physical size
    
    file_key = generate_file_key(current_user.id, file_hash)
    object_name = f"objects/{file_key}"

    # Reset file pointer for upload
    file.file.seek(0)
    
    try:
        # Check if already exists in minio
        minio_client.stat_object("rxncommons-bucket", object_name)
    except Exception:
        # Upload if not exists
        minio_client.put_object(
            "rxncommons-bucket",
            object_name,
            file.file,
            length=file_size,
            part_size=10*1024*1024
        )

    # Database operations
    try:
        # 1. Create or get physical object
        phys_obj = crud_file.get_or_create_physical_object(db, file_key, current_user.id, file_size)
        
        # 2. Create logical dataset_files entry
        new_file = crud_file.create_dataset_file(
            db=db,
            dataset_id=dataset_id,
            version_id=version.id,
            file_key=file_key,
            filename=file.filename,
            file_size=file_size
        )
        
        # 3. Increment ref count
        crud_file.increment_ref_count(db, file_key)
        db.commit()
        db.refresh(new_file)
        
        # Trigger background processing
        background_tasks.add_task(process_file_metadata, new_file.id)

        
        return FileUploadResponse(
            id=new_file.id,
            dataset_id=new_file.dataset_id,
            version_id=new_file.version_id,
            filename=new_file.filename,
            file_size=new_file.file_size,
            upload_status=phys_obj.upload_status
        )
    except ValueError as ve:
        db.rollback()
        if str(ve) == "duplicate_filename":
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "duplicate_filename",
                    "filename": file.filename,
                    "version_num": version_num,
                }
            )
        raise HTTPException(status_code=500, detail=str(ve))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{file_id}/preview", response_model=PreviewResponse)
def preview_file(
    dataset_id: UUID,
    file_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User | None = Depends(deps.get_current_user_optional),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
    dataset = _ensure_dataset_readable(db, dataset_id, current_user, dataset_access_token)
    dataset_file = db.query(DatasetFile).filter(
        DatasetFile.id == file_id,
        DatasetFile.dataset_id == dataset_id
    ).first()
    if not dataset_file:
        raise HTTPException(status_code=404, detail="File not found")
    version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_file.version_id).first()
    if not version or not _can_view_version_for_dataset(dataset, version, current_user):
        raise HTTPException(status_code=404, detail="File not found")

    tmp_path = None
    response = None
    try:
        response = minio_client.get_object("rxncommons-bucket", f"objects/{dataset_file.file_key}")
        suffix = os.path.splitext(dataset_file.filename)[1] or '.tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in response.stream(32 * 1024):
                tmp.write(chunk)
            tmp_path = tmp.name

        preview_type, columns, rows = _load_preview_rows(tmp_path, dataset_file.filename)
        return PreviewResponse(
            filename=dataset_file.filename,
            columns=[str(c) for c in columns],
            rows=rows,
            preview_type=preview_type,
            truncated=len(rows) >= 50,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not preview file: {e}")
    finally:
        if response is not None:
            try:
                response.close()
                response.release_conn()
            except Exception:
                pass
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.get("/{file_id}/metadata", response_model=FileMetadataResponse)
def get_file_metadata(
    dataset_id: UUID,
    file_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")

    dataset_file = db.query(DatasetFile).filter(
        DatasetFile.id == file_id,
        DatasetFile.dataset_id == dataset_id
    ).first()
    if not dataset_file:
        raise HTTPException(status_code=404, detail="File not found")

    phys_obj = db.query(PhysicalStorageObject).filter(
        PhysicalStorageObject.file_key == dataset_file.file_key
    ).first()
    columns = db.query(FileColumn).filter(FileColumn.file_id == file_id).order_by(FileColumn.column_name.asc()).all()
    return FileMetadataResponse(
        file_id=file_id,
        description=dataset_file.description,
        upload_status=phys_obj.upload_status if phys_obj else "pending",
        row_count=dataset_file.row_count,
        error_message=dataset_file.error_message,
        columns=[
            {
                "column_name": c.column_name,
                "column_type": c.column_type,
                "description": c.description or "",
            }
            for c in columns
        ]
    )


@router.put("/{file_id}/metadata", response_model=FileMetadataResponse)
def update_file_metadata(
    dataset_id: UUID,
    file_id: UUID,
    req: FileMetadataUpdateReq,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
    _ensure_dataset_editable(dataset)

    dataset_file = db.query(DatasetFile).filter(
        DatasetFile.id == file_id,
        DatasetFile.dataset_id == dataset_id
    ).first()
    if not dataset_file:
        raise HTTPException(status_code=404, detail="File not found")

    version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_file.version_id).first()
    if not version or version.status != 'draft':
        raise HTTPException(status_code=409, detail="version_not_editable")

    if req.description is not None:
        dataset_file.description = req.description

    for col in req.columns:
        db_col = db.query(FileColumn).filter(
            FileColumn.file_id == file_id,
            FileColumn.column_name == col.column_name
        ).first()
        if db_col:
            db_col.description = col.description

    db.commit()

    columns = db.query(FileColumn).filter(FileColumn.file_id == file_id).order_by(FileColumn.column_name.asc()).all()
    phys_obj = db.query(PhysicalStorageObject).filter(
        PhysicalStorageObject.file_key == dataset_file.file_key
    ).first()
    return FileMetadataResponse(
        file_id=file_id,
        description=dataset_file.description,
        upload_status=phys_obj.upload_status if phys_obj else "pending",
        row_count=dataset_file.row_count,
        error_message=dataset_file.error_message,
        columns=[
            {
                "column_name": c.column_name,
                "column_type": c.column_type,
                "description": c.description or "",
            }
            for c in columns
        ]
    )

@router.get("/{file_id}/download")
def download_file(
    dataset_id: UUID,
    file_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User | None = Depends(deps.get_current_user_optional),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
    dataset_access_token_q: str | None = Query(default=None, alias="dataset_access_token"),
):
    access_token = dataset_access_token or dataset_access_token_q
    dataset = _ensure_dataset_readable(db, dataset_id, current_user, access_token)
    dataset_file = db.query(DatasetFile).filter(
        DatasetFile.id == file_id,
        DatasetFile.dataset_id == dataset_id,
    ).first()
    if not dataset_file:
        raise HTTPException(status_code=404, detail="File not found")
    version = db.query(DatasetVersion).filter(DatasetVersion.id == dataset_file.version_id).first()
    if not version or not _can_view_version_for_dataset(dataset, version, current_user):
        raise HTTPException(status_code=404, detail="File not found")

    # Stream the file directly from MinIO through the backend
    try:
        response = minio_client.get_object("rxncommons-bucket", f"objects/{dataset_file.file_key}")
        encoded_filename = quote(dataset_file.filename)
        return StreamingResponse(
            response.stream(32 * 1024),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Length": str(dataset_file.file_size),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not download file: {e}")


@router.delete("/{file_id}")
def delete_file(
    dataset_id: UUID,
    file_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    if dataset.owner_id != current_user.id and current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
    _ensure_dataset_editable(dataset)

    target_file = db.query(DatasetFile).filter(
        DatasetFile.id == file_id,
        DatasetFile.dataset_id == dataset_id
    ).first()
    if not target_file:
        raise HTTPException(status_code=404, detail="File not found")
    version = db.query(DatasetVersion).filter(DatasetVersion.id == target_file.version_id).first()
    if not version or version.status != 'draft':
        raise HTTPException(status_code=409, detail="version_not_editable")

    deleted = crud_file.delete_dataset_file(db, dataset_id, file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="File not found")

    db.commit()
    return {"status": "success", "file_id": str(file_id)}
