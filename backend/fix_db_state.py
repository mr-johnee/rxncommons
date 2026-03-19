from app.core.database import SessionLocal
from app.models.dataset import Dataset, DatasetVersion
from app.models.review import DatasetReviewRequest
from sqlalchemy.orm import Session

db = SessionLocal()
datasets = db.query(Dataset).all()
for ds in datasets:
    # check if dataset has an approved version
    has_approved = any(v.status == 'published' for v in db.query(DatasetVersion).filter_by(dataset_id=ds.id).all())
    
    if has_approved and ds.dataset_status != 'published':
        print(f"Fixing dataset {ds.id} status from {ds.dataset_status} to published")
        ds.dataset_status = 'published'

db.commit()
db.close()
