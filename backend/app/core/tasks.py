from uuid import UUID
import zipfile
import tempfile
import os
import pandas as pd
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.storage import minio_client
from app.models.dataset import DatasetVersion, DatasetFile, FileColumn
from app.models.storage import PhysicalStorageObject
from fastapi.logger import logger

def process_file_metadata(file_id: UUID):
    with SessionLocal() as db:
        dataset_file = db.query(DatasetFile).filter(DatasetFile.id == file_id).first()
        if not dataset_file:
            return
            
        phys_obj = db.query(PhysicalStorageObject).filter(PhysicalStorageObject.file_key == dataset_file.file_key).first()
        if not phys_obj:
            return
        phys_obj.upload_status = 'pending'
        dataset_file.error_message = None
        db.commit()

        filename = dataset_file.filename.lower()
        if not (filename.endswith('.csv') or filename.endswith('.xlsx') or filename.endswith('.xls')):
            phys_obj.upload_status = 'ready'
            db.commit()
            return

        try:
            # Download temporarily
            response = minio_client.get_object("rxncommons-bucket", f"objects/{dataset_file.file_key}")
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
                for chunk in response.stream(32*1024):
                    tmp.write(chunk)
                tmp_path = tmp.name

            # Extract info safely
            row_count = 0
            columns = []
            if filename.endswith('.csv'):
                chunks = pd.read_csv(tmp_path, chunksize=10000)
                first_chunk = None
                for idx, chunk in enumerate(chunks):
                    if idx == 0:
                        first_chunk = chunk
                    row_count += len(chunk)
                if first_chunk is not None:
                    columns = [(str(c), str(first_chunk[c].dtype)) for c in first_chunk.columns]
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(tmp_path, engine='openpyxl')
                row_count = len(df)
                columns = [(str(c), str(df[c].dtype)) for c in df.columns]
            elif filename.endswith('.xls'):
                df = pd.read_excel(tmp_path, engine='xlrd')
                row_count = len(df)
                columns = [(str(c), str(df[c].dtype)) for c in df.columns]

            # Save row_count and inferred columns
            dataset_file.row_count = row_count
            dataset_file.error_message = None
            db.query(FileColumn).filter(FileColumn.file_id == dataset_file.id).delete()
            for col_name, col_type in columns:
                db.add(FileColumn(
                    file_id=dataset_file.id,
                    dataset_id=dataset_file.dataset_id,
                    column_name=col_name,
                    column_type=col_type,
                    description=''
                ))

            phys_obj.upload_status = 'ready'
            db.commit()

        except Exception as e:
            logger.error(f"Error processing file {file_id}: {e}")
            phys_obj.upload_status = 'error'
            dataset_file.error_message = str(e)
            db.commit()
        finally:
            if 'response' in locals():
                try:
                    response.close()
                    response.release_conn()
                except Exception:
                    pass
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                os.remove(tmp_path)

def pack_version_archive(version_id: UUID):
    with SessionLocal() as db:
        version = db.query(DatasetVersion).filter(DatasetVersion.id == version_id).first()
        if not version:
            return
            
        files = db.query(DatasetFile).filter(DatasetFile.version_id == version_id).all()
        if not files:
            return

        # Create temporary zip
        zip_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp_zip:
                zip_path = tmp_zip.name
                with zipfile.ZipFile(tmp_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for f in files:
                        res = minio_client.get_object("rxncommons-bucket", f"objects/{f.file_key}")
                        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
                            for chunk in res.stream(32*1024):
                                tmp_file.write(chunk)
                            tmp_file_path = tmp_file.name
                        zf.write(tmp_file_path, arcname=f.filename)
                        os.remove(tmp_file_path)

            # Upload zip to MinIO
            zip_size = os.path.getsize(zip_path)
            archive_key = f"archives/version_{version_id}.zip"
            with open(zip_path, 'rb') as f_in:
                minio_client.put_object(
                    "rxncommons-bucket",
                    archive_key,
                    f_in,
                    length=zip_size
                )

            # Save reference
            version.archive_key = archive_key
            db.commit()

        except Exception as e:
            logger.error(f"Failed to pack archive for version {version_id}: {e}")
        finally:
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
