from sqlalchemy.orm import Session
from app.models.storage import PhysicalStorageObject
from app.models.dataset import DatasetFile, DatasetVersion, Dataset
import uuid
from uuid import UUID

def get_or_create_physical_object(db: Session, file_key: str, owner_id: UUID, file_size: int):
    obj = db.query(PhysicalStorageObject).filter(PhysicalStorageObject.file_key == file_key).first()
    if not obj:
        obj = PhysicalStorageObject(
            file_key=file_key,
            owner_id=owner_id,
            file_size=file_size,
            ref_count=0,
            upload_status='pending'
        )
        db.add(obj)
        db.flush()
    return obj

def increment_ref_count(db: Session, file_key: str):
    obj = db.query(PhysicalStorageObject).filter(PhysicalStorageObject.file_key == file_key).with_for_update().first()
    if obj:
        obj.ref_count += 1
        db.add(obj)
        db.flush()
    return obj


def decrement_ref_count(db: Session, file_key: str):
    obj = db.query(PhysicalStorageObject).filter(PhysicalStorageObject.file_key == file_key).with_for_update().first()
    if obj:
        obj.ref_count = max((obj.ref_count or 0) - 1, 0)
        if obj.ref_count == 0:
            # Remove physical object once it is no longer referenced by any logical file.
            try:
                from app.core.storage import minio_client
                minio_client.remove_object("rxncommons-bucket", f"objects/{file_key}")
            except Exception:
                # Keep DB record if storage deletion fails so it can be retried later.
                pass
            else:
                db.delete(obj)
                db.flush()
                return obj
        db.add(obj)
        db.flush()
    return obj

def create_dataset_file(db: Session, dataset_id: UUID, version_id: UUID, file_key: str, filename: str, file_size: int):
    # Check if a file with the same filename already exists in this version
    existing = db.query(DatasetFile).filter(
        DatasetFile.version_id == version_id,
        DatasetFile.filename == filename
    ).first()
    if existing:
        raise ValueError("duplicate_filename")
    
    new_file = DatasetFile(
        dataset_id=dataset_id,
        version_id=version_id,
        file_key=file_key,
        filename=filename,
        file_size=file_size
    )
    db.add(new_file)
    db.flush()
    return new_file

def get_version_by_num(db: Session, dataset_id: UUID, version_num: int):
    return db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.version_num == version_num
    ).first()


def delete_dataset_file(db: Session, dataset_id: UUID, file_id: UUID):
    dataset_file = db.query(DatasetFile).filter(
        DatasetFile.dataset_id == dataset_id,
        DatasetFile.id == file_id
    ).first()
    if not dataset_file:
        return None

    file_key = dataset_file.file_key
    db.delete(dataset_file)
    db.flush()
    decrement_ref_count(db, file_key)
    return dataset_file
