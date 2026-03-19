from sqlalchemy.orm import Session
from app.models.dataset import DatasetVersion
from app.models.dataset import DatasetFile, FileColumn
from app.models.storage import PhysicalStorageObject
from uuid import UUID
from app.crud import crud_file

def get_versions(db: Session, dataset_id: UUID):
    return db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version_num.desc()).all()

def _inherit_files_from_base(
    db: Session,
    dataset_id: UUID,
    target_version_id: UUID,
    base_version_num: int | None,
):
    if base_version_num is None:
        return

    base_v = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.version_num == base_version_num
    ).first()
    if not base_v:
        return

    base_files = db.query(DatasetFile).filter(DatasetFile.version_id == base_v.id).all()
    for old_file in base_files:
        new_file = DatasetFile(
            dataset_id=dataset_id,
            version_id=target_version_id,
            file_key=old_file.file_key,
            filename=old_file.filename,
            description=old_file.description,
            row_count=old_file.row_count,
            file_size=old_file.file_size,
            error_message=old_file.error_message,
        )
        db.add(new_file)
        db.flush()

        old_columns = db.query(FileColumn).filter(FileColumn.file_id == old_file.id).all()
        for col in old_columns:
            db.add(FileColumn(
                file_id=new_file.id,
                dataset_id=dataset_id,
                column_name=col.column_name,
                column_type=col.column_type,
                description=col.description,
            ))

        storage_obj = db.query(PhysicalStorageObject).filter(
            PhysicalStorageObject.file_key == old_file.file_key
        ).with_for_update().first()
        if storage_obj:
            storage_obj.ref_count += 1
            db.add(storage_obj)


def _reset_draft_files(db: Session, dataset_id: UUID, draft_version_id: UUID):
    file_ids = [
        row.id for row in db.query(DatasetFile.id).filter(
            DatasetFile.dataset_id == dataset_id,
            DatasetFile.version_id == draft_version_id
        ).all()
    ]
    for file_id in file_ids:
        crud_file.delete_dataset_file(db, dataset_id, file_id)


def create_version(
    db: Session,
    dataset_id: UUID,
    current_user_id: UUID,
    base_version_num: int = None,
    reset_existing_draft: bool = False,
):
    # 同一数据集只保留一个草稿版本。
    existing_draft = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.status == 'draft'
    ).order_by(DatasetVersion.version_num.desc()).first()

    latest = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id
    ).order_by(DatasetVersion.version_num.desc()).first()
    latest_published = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.status == 'published'
    ).order_by(DatasetVersion.version_num.desc()).first()
    base_num = base_version_num if base_version_num is not None else (
        latest_published.version_num if latest_published else (latest.version_num if latest else None)
    )

    if existing_draft:
        # Prefer preserving same-base draft; otherwise reset draft to requested base
        # to avoid carrying unrelated files from old draft attempts.
        draft_base_num = existing_draft.base_version_num
        if draft_base_num is None and existing_draft.version_num > 1:
            draft_base_num = existing_draft.version_num - 1

        if not reset_existing_draft and (base_num is None or draft_base_num == base_num):
            return existing_draft
        if base_num is not None and draft_base_num == base_num:
            return existing_draft

        _reset_draft_files(db, dataset_id, existing_draft.id)
        existing_draft.base_version_num = base_num
        existing_draft.version_note = None
        existing_draft.change_manifest = {}
        existing_draft.metadata_complete = False
        existing_draft.archive_key = None
        existing_draft.status = 'draft'

        _inherit_files_from_base(db, dataset_id, existing_draft.id, base_num)
        db.commit()
        db.refresh(existing_draft)
        return existing_draft

    new_num = latest.version_num + 1 if latest else 1
    new_v = DatasetVersion(
        dataset_id=dataset_id,
        version_num=new_num,
        status='draft',
        base_version_num=base_num,
    )
    db.add(new_v)
    db.flush()

    _inherit_files_from_base(db, dataset_id, new_v.id, base_num)

    db.commit()
    db.refresh(new_v)
    return new_v
