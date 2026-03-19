from app.core.database import SessionLocal
from app.models.dataset import DatasetReviewRequest
db = SessionLocal()
reqs = db.query(DatasetReviewRequest).all()
print(f"Total reqs: {len(reqs)}")
for r in reqs:
    print(r.id, r.status)
