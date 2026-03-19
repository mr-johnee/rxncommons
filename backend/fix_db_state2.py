from app.core.database import SessionLocal
from app.models.dataset import Dataset, DatasetVersion
from app.models.review import DatasetReviewRequest
from sqlalchemy.orm import Session

db = SessionLocal()

# Find any dataset that has at least one 'published' version, 
# but whose dataset_status is 'pending_review' or 'draft'
datasets = db.query(Dataset).all()
count = 0
for ds in datasets:
    versions = db.query(DatasetVersion).filter_by(dataset_id=ds.id).all()
    has_approved = any(v.status == 'published' for v in versions)
    
    if has_approved and ds.dataset_status != 'published':
        print(f"Fixing dataset {ds.id} status from {ds.dataset_status} to published")
        ds.dataset_status = 'published'
        count += 1

db.commit()
print(f"Fixed {count} datasets")
db.close()
