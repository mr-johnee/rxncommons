from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.api import deps
from app.models.dataset import Dataset, DatasetVersion, DatasetFile
from app.core.dataset_access import public_dataset_visible_filter
from app.models.user import User

router = APIRouter()

@router.get("/overview")
def get_stats_overview(db: Session = Depends(deps.get_db)):
    dataset_count = db.query(Dataset).filter(
        Dataset.deleted_at.is_(None),
        public_dataset_visible_filter(db),
    ).count()
    user_count = db.query(User).filter(User.is_active == True).count()

    latest_published_version_subq = (
        db.query(
            DatasetVersion.dataset_id.label("dataset_id"),
            func.max(DatasetVersion.version_num).label("version_num"),
        )
        .join(Dataset, Dataset.id == DatasetVersion.dataset_id)
        .filter(
            Dataset.deleted_at.is_(None),
            public_dataset_visible_filter(db),
            DatasetVersion.status == "published",
        )
        .group_by(DatasetVersion.dataset_id)
        .subquery()
    )

    # Sum row_count from each dataset latest published version.
    total_reactions = (
        db.query(func.coalesce(func.sum(DatasetFile.row_count), 0))
        .join(DatasetVersion, DatasetVersion.id == DatasetFile.version_id)
        .join(
            latest_published_version_subq,
            and_(
                latest_published_version_subq.c.dataset_id == DatasetVersion.dataset_id,
                latest_published_version_subq.c.version_num == DatasetVersion.version_num,
            ),
        )
        .scalar()
    ) or 0

    return {
        "dataset_count": dataset_count,
        "total_reactions": int(total_reactions),
        "user_count": user_count,
        # Compatibility keys for old frontend code
        "datasets": dataset_count,
        "reactions": int(total_reactions),
        "users": user_count,
    }
