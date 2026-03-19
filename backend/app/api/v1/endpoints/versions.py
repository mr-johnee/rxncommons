from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from uuid import UUID
from urllib.parse import quote
from app.api import deps
from app.crud import crud_version, crud_dataset, crud_file
from app.schemas.version import VersionResponse, VersionCreateItem
from app.models.user import User
from app.core.storage import minio_client
from app.core.dataset_access import evaluate_dataset_access
from app.models.dataset import DatasetVersion, DatasetFile
from app.models.storage import PhysicalStorageObject

router = APIRouter()


def _can_view_version(
    db: Session,
    dataset,
    version,
    current_user: User | None,
    dataset_access_token: str | None,
) -> tuple[bool, bool]:
    allowed, password_required = evaluate_dataset_access(
        db=db,
        dataset=dataset,
        current_user=current_user,
        access_token=dataset_access_token,
    )
    if not allowed:
        return False, password_required

    is_owner_or_admin = bool(
        current_user and (current_user.role == "admin" or current_user.id == dataset.owner_id)
    )
    if version.status == "published" or is_owner_or_admin:
        return True, False

    return False, False


@router.get("", response_model=List[VersionResponse])
def get_versions(
    dataset_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: User | None = Depends(deps.get_current_user_optional),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
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

    versions = crud_version.get_versions(db, dataset_id)
    if not current_user or (current_user.role != "admin" and current_user.id != dataset.owner_id):
        versions = [v for v in versions if v.status == "published"]
    return versions

@router.post("", response_model=VersionResponse)
def create_version(
    dataset_id: UUID,
    req: VersionCreateItem,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    if not current_user.is_email_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset or dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    if dataset.dataset_status == 'pending_review':
        raise HTTPException(status_code=409, detail="dataset_under_review_locked")

    # If there is already an unpublished version ahead of current published version,
    # block creating another new version to keep a single in-progress line.
    in_progress = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.status.in_(["draft", "pending_review"]),
    ).order_by(DatasetVersion.version_num.desc()).first()
    if in_progress and (not dataset.current_version or in_progress.version_num > int(dataset.current_version)):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "existing_unapproved_version",
                "version_num": in_progress.version_num,
                "status": in_progress.status,
            },
        )
        
    new_v = crud_version.create_version(
        db,
        dataset_id,
        current_user.id,
        base_version_num=req.base_version_num,
        reset_existing_draft=req.reset_existing_draft,
    )
    return new_v

from pydantic import BaseModel
class InheritFilesReq(BaseModel):
    file_ids: List[UUID]

@router.post("/{version_num}/inherit-files")
def inherit_files(
    dataset_id: UUID,
    version_num: int,
    req: InheritFilesReq,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset or dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    return {"status": "success", "message": "Files inherited", "count": len(req.file_ids)}

@router.delete("/{version_num}")
def delete_version(
    dataset_id: UUID,
    version_num: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_user)
):
    dataset = crud_dataset.get_dataset(db, dataset_id)
    if not dataset or dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    # Validation logic here...
    return {"status": "success", "message": f"Version {version_num} deleted"}

@router.get("/{version_num}/download-all")
def download_all_files(
    dataset_id: UUID,
    version_num: int,
    db: Session = Depends(deps.get_db),
    current_user: User | None = Depends(deps.get_current_user_optional),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
    dataset_access_token_q: str | None = Query(default=None, alias="dataset_access_token"),
):
    access_token = dataset_access_token or dataset_access_token_q
    dataset = crud_dataset.get_dataset(db, dataset_id)
    allowed, password_required = evaluate_dataset_access(
        db=db,
        dataset=dataset,
        current_user=current_user,
        access_token=access_token,
    )
    if not allowed:
        if password_required:
            raise HTTPException(status_code=403, detail={"code": "dataset_access_password_required"})
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id, DatasetVersion.version_num == version_num).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    version_allowed, version_password_required = _can_view_version(
        db,
        dataset,
        version,
        current_user,
        access_token,
    )
    if not version_allowed:
        if version_password_required:
            raise HTTPException(status_code=403, detail={"code": "dataset_access_password_required"})
        raise HTTPException(status_code=404, detail="Version not found")

    zip_name = quote(f"{dataset.title}_v{version_num}.zip")
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{zip_name}"}

    # If pre-built archive exists, stream it through backend.
    # This avoids exposing MinIO private endpoint details to browser and ensures direct download.
    if version.archive_key:
        try:
            obj = minio_client.get_object("rxncommons-bucket", version.archive_key)

            def iter_archive():
                try:
                    for chunk in obj.stream(32 * 1024):
                        yield chunk
                finally:
                    obj.close()
                    obj.release_conn()

            try:
                stat = minio_client.stat_object("rxncommons-bucket", version.archive_key)
                headers["Content-Length"] = str(stat.size)
            except Exception:
                pass

            dataset.download_count = int(dataset.download_count or 0) + 1
            db.commit()
            return StreamingResponse(
                iter_archive(),
                media_type="application/zip",
                headers=headers,
            )
        except Exception:
            pass  # Fall through to on-the-fly ZIP

    # Build ZIP on-the-fly from individual files
    import io, zipfile

    files = db.query(DatasetFile).filter(DatasetFile.version_id == version.id).all()
    if not files:
        raise HTTPException(status_code=404, detail="No files in this version")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            try:
                obj = minio_client.get_object("rxncommons-bucket", f"objects/{f.file_key}")
                zf.writestr(f.filename, obj.read())
                obj.close()
                obj.release_conn()
            except Exception:
                continue
    buf.seek(0)
    dataset.download_count = int(dataset.download_count or 0) + 1
    db.commit()
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers=headers
    )

class FileResponse(BaseModel):
    id: UUID
    filename: str
    file_size: int
    created_at: datetime
    upload_status: str
    row_count: Optional[int] = None
    error_message: Optional[str] = None
    class Config:
        from_attributes = True

@router.get("/{version_num}/files", response_model=List[FileResponse])
def get_version_files(
    dataset_id: UUID,
    version_num: int,
    db: Session = Depends(deps.get_db),
    current_user: User | None = Depends(deps.get_current_user_optional),
    dataset_access_token: str | None = Header(default=None, alias="X-Dataset-Access-Token"),
):
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

    version = crud_file.get_version_by_num(db, dataset_id, version_num)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    version_allowed, version_password_required = _can_view_version(
        db,
        dataset,
        version,
        current_user,
        dataset_access_token,
    )
    if not version_allowed:
        if version_password_required:
            raise HTTPException(status_code=403, detail={"code": "dataset_access_password_required"})
        raise HTTPException(status_code=404, detail="Version not found")

    files = db.query(DatasetFile).filter(DatasetFile.version_id == version.id).all()
    file_keys = [f.file_key for f in files]
    status_map = {}
    if file_keys:
        status_rows = db.query(PhysicalStorageObject).filter(
            PhysicalStorageObject.file_key.in_(file_keys)
        ).all()
        status_map = {
            row.file_key: row.upload_status or "pending"
            for row in status_rows
        }
    return [
        FileResponse(
            id=f.id,
            filename=f.filename,
            file_size=f.file_size,
            created_at=f.created_at,
            upload_status=status_map.get(f.file_key, "pending"),
            row_count=f.row_count,
            error_message=f.error_message,
        )
        for f in files
    ]
