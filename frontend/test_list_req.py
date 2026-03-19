from app.core.database import SessionLocal
from app.models.interaction import DatasetReviewRequest
from sqlalchemy import func, and_

db = SessionLocal()

# Subquery for latest review request per dataset
subquery = db.query(
    DatasetReviewRequest.dataset_id,
    func.max(DatasetReviewRequest.submitted_at).label('max_time')
).group_by(DatasetReviewRequest.dataset_id).subquery()

# Main query joining with subquery to get only latest request rows
query = db.query(DatasetReviewRequest).join(
    subquery,
    and_(
        DatasetReviewRequest.dataset_id == subquery.c.dataset_id,
        DatasetReviewRequest.submitted_at == subquery.c.max_time
    )
)

print([r.id for r in query.all()])
