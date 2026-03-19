from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from app.models.dataset import Dataset, DatasetVersion, DatasetTag, DatasetFile
from app.models.interaction import DatasetReviewRequest
from app.core.dataset_access import attach_access_levels, public_dataset_visible_filter
from app.schemas.dataset import DatasetCreate
from datetime import datetime
import re
import uuid

PUBLIC_VISIBLE_STATUSES = ['published']

def _clean_slug(title: str, short_id: str) -> str:
    # 统一小写
    slug = title.lower()
    # 空格和分隔符（空格、-、.）统一替换为 _
    slug = re.sub(r'[\s\-.]+', '_', slug)
    # 其他字符（如 /、#、%、中文符号）移除或替换为 _ (此处我们非小写字母数字的全部去除非下划线字符)
    slug = re.sub(r'[^a-z0-9_]', '', slug)
    # 合并连续 _，并去除首尾
    slug = re.sub(r'_+', '_', slug).strip('_')
    # 超长截断 (保留充足空间给可能得后缀)
    slug = slug[:90]
    
    # 若清洗后为空，回退为 dataset_{short_id}
    if not slug:
        slug = f"dataset_{short_id}"
    return slug


def generate_unique_slug(
    db: Session,
    owner_id: uuid.UUID,
    title: str,
    exclude_dataset_id: uuid.UUID | None = None,
) -> str:
    short_id = str(uuid.uuid4())[:8]
    base_slug = _clean_slug(title, short_id)
    slug = base_slug
    suffix = 2

    while True:
        q = db.query(Dataset).filter(
            Dataset.owner_id == owner_id,
            Dataset.slug == slug,
            Dataset.deleted_at.is_(None)
        )
        if exclude_dataset_id is not None:
            q = q.filter(Dataset.id != exclude_dataset_id)
        if q.first() is None:
            return slug
        slug = f"{base_slug}_{suffix}"
        suffix += 1

def create_dataset(db: Session, *, dataset_in: DatasetCreate, owner_id: uuid.UUID) -> Dataset:
    slug = generate_unique_slug(db, owner_id=owner_id, title=dataset_in.title)

    # 1. 创建数据集框架，初始状态草稿 draft
    db_dataset = Dataset(
        owner_id=owner_id,
        slug=slug,
        title=dataset_in.title,
        description=dataset_in.description,
        source_type=dataset_in.source_type,
        source_ref=dataset_in.source_ref,
        license=dataset_in.license,
        dataset_status='draft',
    )
    
    db.add(db_dataset)
    db.flush() # 将 INSERT 刷入 DB 以获取 id

    # 2. 自动创建版本 V1 数据
    db_version = DatasetVersion(
        dataset_id=db_dataset.id,
        version_num=1,
        status='draft'
    )
    db.add(db_version)
    
    # 单独事物提交
    db.commit()
    db.refresh(db_dataset)
    
    return db_dataset
def get_dataset(db: Session, dataset_id: uuid.UUID) -> Dataset:
    return db.query(Dataset).filter(Dataset.id == dataset_id).first()

def get_datasets(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    search: str = None,
    owner_id=None,
    include_private: bool = False,
    source_type: str | None = None,
    status_filter: str | None = None,
    size_bucket: str | None = None,
    min_rows: int | None = None,
    max_rows: int | None = None,
    sort_order: str | None = None,
):
    query = db.query(Dataset).filter(Dataset.deleted_at.is_(None))
    
    if search:
        like = f"%{search.lower()}%"
        query = query.outerjoin(DatasetTag, DatasetTag.dataset_id == Dataset.id).filter(
            or_(
                func.lower(Dataset.title).like(like),
                func.lower(DatasetTag.tag).like(like),
            )
        ).distinct()

    if source_type:
        query = query.filter(Dataset.source_type.ilike(f'%{source_type}%'))

    if status_filter:
        query = query.filter(Dataset.dataset_status == status_filter)

    if not owner_id and not include_private:
        current_version_id_subq = (
            db.query(DatasetVersion.id)
            .filter(
                DatasetVersion.dataset_id == Dataset.id,
                DatasetVersion.status == 'published',
            )
            .order_by(DatasetVersion.version_num.desc())
            .limit(1)
            .correlate(Dataset)
            .scalar_subquery()
        )
    else:
        current_version_id_subq = db.query(DatasetVersion.id).filter(
            DatasetVersion.dataset_id == Dataset.id,
            DatasetVersion.version_num == Dataset.current_version,
        ).correlate(Dataset).scalar_subquery()
    total_rows_subq = db.query(func.coalesce(func.sum(DatasetFile.row_count), 0)).filter(
        DatasetFile.version_id == current_version_id_subq
    ).correlate(Dataset).scalar_subquery()

    if size_bucket:

        # 小/中/大：<1000条, 1000~10万条, >10万条
        if size_bucket == 'small':
            query = query.filter(total_rows_subq < 1000)
        elif size_bucket == 'medium':
            query = query.filter(total_rows_subq >= 1000, total_rows_subq <= 100000)
        elif size_bucket == 'large':
            query = query.filter(total_rows_subq > 100000)

    if min_rows is not None:
        query = query.filter(total_rows_subq >= min_rows)
    if max_rows is not None:
        query = query.filter(total_rows_subq <= max_rows)
    
    if owner_id:
        query = query.filter(Dataset.owner_id == owner_id)
    elif not include_private:
        query = query.filter(Dataset.dataset_status.in_(PUBLIC_VISIBLE_STATUSES))
        query = query.filter(public_dataset_visible_filter(db))
    
    total = query.count()
    if sort_order == "oldest":
        query = query.order_by(Dataset.created_at.asc(), Dataset.id.asc())
    else:
        query = query.order_by(Dataset.created_at.desc(), Dataset.id.desc())
    items = query.offset(skip).limit(limit).all()

    if items:
        attach_access_levels(db, items)
        dataset_ids = [d.id for d in items]
        if not owner_id and not include_private:
            latest_pub_subq = (
                db.query(
                    DatasetVersion.dataset_id.label('dataset_id'),
                    func.max(DatasetVersion.version_num).label('version_num'),
                )
                .filter(
                    DatasetVersion.dataset_id.in_(dataset_ids),
                    DatasetVersion.status == 'published',
                )
                .group_by(DatasetVersion.dataset_id)
                .subquery()
            )
            rows_agg = (
                db.query(
                    DatasetVersion.dataset_id,
                    func.coalesce(func.sum(DatasetFile.row_count), 0).label('total_rows')
                )
                .join(
                    latest_pub_subq,
                    and_(
                        latest_pub_subq.c.dataset_id == DatasetVersion.dataset_id,
                        latest_pub_subq.c.version_num == DatasetVersion.version_num,
                    ),
                )
                .join(
                    DatasetFile,
                    DatasetFile.version_id == DatasetVersion.id,
                    isouter=True,
                )
                .group_by(DatasetVersion.dataset_id)
                .all()
            )
        else:
            rows_agg = (
                db.query(
                    DatasetVersion.dataset_id,
                    func.coalesce(func.sum(DatasetFile.row_count), 0).label('total_rows')
                )
                .join(
                    Dataset,
                    Dataset.id == DatasetVersion.dataset_id,
                )
                .join(
                    DatasetFile,
                    DatasetFile.version_id == DatasetVersion.id,
                    isouter=True,
                )
                .filter(
                    DatasetVersion.dataset_id.in_(dataset_ids),
                    DatasetVersion.version_num == Dataset.current_version,
                )
                .group_by(DatasetVersion.dataset_id)
                .all()
            )
        rows_map = {row.dataset_id: int(row.total_rows or 0) for row in rows_agg}

        # Compute latest submitted/reviewed timestamps independently.
        review_submitted_rows = (
            db.query(
                DatasetReviewRequest.dataset_id,
                func.max(DatasetReviewRequest.submitted_at).label('latest_submitted_at'),
            )
            .filter(DatasetReviewRequest.dataset_id.in_(dataset_ids))
            .group_by(DatasetReviewRequest.dataset_id)
            .all()
        )

        review_reviewed_rows = (
            db.query(
                DatasetReviewRequest.dataset_id,
                func.max(DatasetReviewRequest.reviewed_at).label('latest_reviewed_at'),
            )
            .filter(DatasetReviewRequest.dataset_id.in_(dataset_ids))
            .group_by(DatasetReviewRequest.dataset_id)
            .all()
        )
        review_approved_rows = (
            db.query(
                DatasetReviewRequest.dataset_id,
                func.max(DatasetReviewRequest.reviewed_at).label('latest_approved_at'),
            )
            .filter(
                DatasetReviewRequest.dataset_id.in_(dataset_ids),
                DatasetReviewRequest.status == 'approved',
            )
            .group_by(DatasetReviewRequest.dataset_id)
            .all()
        )
        latest_submitted_map = {row.dataset_id: row.latest_submitted_at for row in review_submitted_rows}
        latest_reviewed_map = {row.dataset_id: row.latest_reviewed_at for row in review_reviewed_rows}
        latest_approved_map = {row.dataset_id: row.latest_approved_at for row in review_approved_rows}
        latest_editable_rows = (
            db.query(
                DatasetVersion.dataset_id,
                DatasetVersion.version_num,
                DatasetVersion.status,
            )
            .filter(
                DatasetVersion.dataset_id.in_(dataset_ids),
                DatasetVersion.status.in_(["draft", "revision_required"]),
            )
            .order_by(DatasetVersion.dataset_id.asc(), DatasetVersion.version_num.desc())
            .all()
        )
        latest_editable_map = {}
        for row in latest_editable_rows:
            if row.dataset_id not in latest_editable_map:
                latest_editable_map[row.dataset_id] = row

        latest_published_rows = (
            db.query(
                DatasetVersion.dataset_id,
                func.max(DatasetVersion.version_num).label("latest_published_version_num"),
            )
            .filter(
                DatasetVersion.dataset_id.in_(dataset_ids),
                DatasetVersion.status == "published",
            )
            .group_by(DatasetVersion.dataset_id)
            .all()
        )
        latest_published_map = {
            row.dataset_id: int(row.latest_published_version_num or 0)
            for row in latest_published_rows
        }

        for item in items:
            setattr(item, 'total_rows', rows_map.get(item.id, 0))
            setattr(item, 'latest_review_submitted_at', latest_submitted_map.get(item.id))
            setattr(item, 'latest_reviewed_at', latest_reviewed_map.get(item.id))
            setattr(item, 'latest_approved_at', latest_approved_map.get(item.id))
            editable_row = latest_editable_map.get(item.id)
            setattr(item, 'latest_editable_version_num', editable_row.version_num if editable_row else None)
            setattr(item, 'latest_editable_version_status', editable_row.status if editable_row else None)
            setattr(item, 'has_published_version', bool(latest_published_map.get(item.id)))

    return items, total

def get_dataset_by_owner_and_slug(db: Session, owner_id: uuid.UUID, slug: str) -> Dataset:
    return db.query(Dataset).filter(
        Dataset.owner_id == owner_id,
        Dataset.slug == slug,
        Dataset.deleted_at.is_(None)
    ).first()


def soft_delete_dataset(
    db: Session,
    *,
    dataset: Dataset,
    deleted_by: uuid.UUID,
) -> None:
    from app.models.system import HomeFeaturedDataset

    dataset.deleted_at = datetime.utcnow()
    dataset.deleted_by = deleted_by
    dataset.dataset_status = "deleted"

    pending_req = db.query(DatasetReviewRequest).filter(
        DatasetReviewRequest.dataset_id == dataset.id,
        DatasetReviewRequest.status == "pending",
    ).first()
    if pending_req:
        pending_req.status = "canceled_by_user"

    db.query(HomeFeaturedDataset).filter(
        HomeFeaturedDataset.dataset_id == dataset.id
    ).delete(synchronize_session=False)


def restore_soft_deleted_dataset(
    db: Session,
    *,
    dataset: Dataset,
) -> str:
    latest_published = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset.id,
        DatasetVersion.status == "published",
    ).order_by(DatasetVersion.version_num.desc()).first()
    if latest_published:
        dataset.dataset_status = "published"
        dataset.current_version = latest_published.version_num
    else:
        latest_revision_required = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset.id,
            DatasetVersion.status == "revision_required",
        ).order_by(DatasetVersion.version_num.desc()).first()
        latest_draft_like = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset.id,
            DatasetVersion.status.in_(["draft", "pending_review"]),
        ).order_by(DatasetVersion.version_num.desc()).first()

        if latest_revision_required:
            dataset.dataset_status = "revision_required"
            dataset.current_version = latest_revision_required.version_num
        elif latest_draft_like:
            dataset.dataset_status = "draft"
            dataset.current_version = latest_draft_like.version_num
        else:
            dataset.dataset_status = "draft"

    dataset.deleted_at = None
    dataset.deleted_by = None
    return dataset.dataset_status


def hard_delete_dataset(
    db: Session,
    *,
    dataset: Dataset,
) -> None:
    from app.crud import crud_file
    from app.core.storage import minio_client

    versions = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset.id
    ).all()
    archive_keys = [v.archive_key for v in versions if v.archive_key]

    file_ids = [
        row.id
        for row in db.query(DatasetFile.id).filter(DatasetFile.dataset_id == dataset.id).all()
    ]
    for file_id in file_ids:
        crud_file.delete_dataset_file(db, dataset.id, file_id)

    for archive_key in archive_keys:
        try:
            minio_client.remove_object("rxncommons-bucket", archive_key)
        except Exception:
            pass

    db.delete(dataset)
    db.flush()


def get_dataset_rows_range(
    db: Session,
    search: str = None,
    owner_id=None,
    include_private: bool = False,
    source_type: str | None = None,
):
    query = db.query(Dataset).filter(Dataset.deleted_at.is_(None))

    if search:
        like = f"%{search.lower()}%"
        query = query.outerjoin(DatasetTag, DatasetTag.dataset_id == Dataset.id).filter(
            or_(
                func.lower(Dataset.title).like(like),
                func.lower(DatasetTag.tag).like(like),
            )
        ).distinct()

    if source_type:
        query = query.filter(Dataset.source_type.ilike(f'%{source_type}%'))

    if owner_id:
        query = query.filter(Dataset.owner_id == owner_id)
    elif not include_private:
        query = query.filter(Dataset.dataset_status.in_(PUBLIC_VISIBLE_STATUSES))
        query = query.filter(public_dataset_visible_filter(db))

    datasets = query.all()
    if not datasets:
        return 0, 0

    dataset_ids = [d.id for d in datasets]
    if not owner_id and not include_private:
        latest_pub_subq = (
            db.query(
                DatasetVersion.dataset_id.label('dataset_id'),
                func.max(DatasetVersion.version_num).label('version_num'),
            )
            .filter(
                DatasetVersion.dataset_id.in_(dataset_ids),
                DatasetVersion.status == 'published',
            )
            .group_by(DatasetVersion.dataset_id)
            .subquery()
        )
        rows_agg = (
            db.query(
                DatasetVersion.dataset_id,
                func.coalesce(func.sum(DatasetFile.row_count), 0).label('total_rows')
            )
            .join(
                latest_pub_subq,
                and_(
                    latest_pub_subq.c.dataset_id == DatasetVersion.dataset_id,
                    latest_pub_subq.c.version_num == DatasetVersion.version_num,
                ),
            )
            .join(
                DatasetFile,
                DatasetFile.version_id == DatasetVersion.id,
                isouter=True,
            )
            .group_by(DatasetVersion.dataset_id)
            .all()
        )
    else:
        rows_agg = (
            db.query(
                DatasetVersion.dataset_id,
                func.coalesce(func.sum(DatasetFile.row_count), 0).label('total_rows')
            )
            .join(
                Dataset,
                Dataset.id == DatasetVersion.dataset_id,
            )
            .join(
                DatasetFile,
                DatasetFile.version_id == DatasetVersion.id,
                isouter=True,
            )
            .filter(
                DatasetVersion.dataset_id.in_(dataset_ids),
                DatasetVersion.version_num == Dataset.current_version,
            )
            .group_by(DatasetVersion.dataset_id)
            .all()
        )

    rows_values = [int(r.total_rows or 0) for r in rows_agg]
    if len(rows_values) < len(dataset_ids):
        rows_values.extend([0] * (len(dataset_ids) - len(rows_values)))

    return min(rows_values), max(rows_values)
