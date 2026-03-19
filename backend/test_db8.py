from app.core.database import SessionLocal
from app.models.dataset import Dataset
from app.models.interaction import DatasetReviewRequest
from app.models.user import User

db = SessionLocal()
owner_alias = User
reqs = db.query(DatasetReviewRequest).join(
    Dataset,
    Dataset.id == DatasetReviewRequest.dataset_id,
).join(
    owner_alias,
    owner_alias.id == Dataset.owner_id,
).filter(DatasetReviewRequest.status == 'approved').all()

for r in reqs:
    print(f"Req: {r.id}, ds status on req?: {getattr(r.dataset, 'dataset_status', None)}")
    print(f"  has dict? {r.__dict__.get('dataset')}")

