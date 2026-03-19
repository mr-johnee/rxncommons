import sys
from app.core.database import SessionLocal
from app.models.dataset import Dataset, DatasetVersion
from app.models.interaction import DatasetReviewRequest

try:
    db = SessionLocal()
    reqs = db.query(DatasetReviewRequest).filter_by(status='approved').all()
    print(f"Total approved reqs: {len(reqs)}")
    for r in reqs:
        ds = db.query(Dataset).filter_by(id=r.dataset_id).first()
        if ds:
            print(f"Req {r.id}: {r.status} | DS {ds.id}: status={ds.dataset_status}")
            for v in db.query(DatasetVersion).filter_by(dataset_id=ds.id).all():
                print(f"  V{v.version_num}: {v.status}")
except Exception as e:
    print(f"ERROR: {e}")
