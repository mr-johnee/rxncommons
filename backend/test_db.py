from app.core.database import SessionLocal
from app.models.review import DatasetReviewRequest
from app.models.dataset import Dataset
db = SessionLocal()
req = db.query(DatasetReviewRequest).filter(DatasetReviewRequest.status == 'approved').first()
ds = db.query(Dataset).filter(Dataset.id == req.dataset_id).first()
print(f"Req: {req.id}, DS Status: {ds.dataset_status}, V: {ds.current_version}")
