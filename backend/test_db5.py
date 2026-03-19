from app.core.database import SessionLocal
from app.models.dataset import Dataset, DatasetVersion, DatasetReviewRequest
db = SessionLocal()
reqs = db.query(DatasetReviewRequest).filter_by(status='approved').all()
for r in reqs:
    ds = db.query(Dataset).filter_by(id=r.dataset_id).first()
    if ds:
        print(f"Req {r.id}: {r.status} | DS {ds.id}: {ds.dataset_status}")
        for v in db.query(DatasetVersion).filter_by(dataset_id=ds.id).all():
            print(f"  V{v.version_num}: {v.status}")
