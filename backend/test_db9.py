from app.core.database import SessionLocal
from app.models.dataset import Dataset
from app.models.interaction import DatasetReviewRequest
from app.models.user import User
from app.schemas.admin import ReviewRequestResponse

db = SessionLocal()
owner_alias = User
r = db.query(DatasetReviewRequest).join(Dataset, Dataset.id == DatasetReviewRequest.dataset_id).first()

print(ReviewRequestResponse.model_validate(r).model_dump())
