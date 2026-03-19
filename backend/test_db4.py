from app.core.database import SessionLocal
from app.models.dataset import Dataset, DatasetVersion
db = SessionLocal()
ds = db.query(Dataset).filter_by(dataset_status='pending_review').first()
if ds:
    versions = db.query(DatasetVersion).filter_by(dataset_id=ds.id).all()
    print(f"DS {ds.id} status={ds.dataset_status}")
    for v in versions:
        print(f"  V{v.version_num} status={v.status}")
