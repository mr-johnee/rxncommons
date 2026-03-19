import sys
import uuid
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
from app.db.session import SessionLocal
from app.models.dataset import Dataset
from app.models.interaction import DatasetReviewRequest

db = SessionLocal()
# list review requests
reqs = db.query(DatasetReviewRequest).all()
print(f"Total reqs: {len(reqs)}")
