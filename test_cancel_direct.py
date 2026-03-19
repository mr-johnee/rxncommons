import uuid
import sys
import traceback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models.dataset import Dataset, DatasetVersion
from backend.app.models.interaction import DatasetReviewRequest
from backend.app.api.v1.endpoints.datasets import _extract_requested_version_num
from datetime import datetime

engine = create_engine('postgresql://rxn_user:rxn_pass_123@localhost:5433/rxncommons')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

try:
    dataset = db.query(Dataset).first()
    if not dataset:
        print("No dataset")
        sys.exit()

    pending_req = db.query(DatasetReviewRequest).filter(
        DatasetReviewRequest.dataset_id == dataset.id
        # DatasetReviewRequest.status == "pending"
    ).with_for_update().first()
    
    if not pending_req:
        print("No pending req")
        sys.exit()

    print(f"Req: {pending_req.id}, result_reason: {pending_req.result_reason}")
    requested_version_num = _extract_requested_version_num(pending_req.result_reason)
    print(f"Version num: {requested_version_num}")
    
    if requested_version_num is not None:
        version = db.query(DatasetVersion).filter(
            DatasetVersion.dataset_id == dataset.id,
            DatasetVersion.version_num == requested_version_num
        ).first()
        if version and version.status == "pending_review":
            version.status = "draft"
            print("Changed version to draft")

    pending_req.status = "canceled_by_user"
    pending_req.reviewed_at = datetime.utcnow()
    # pending_req.reviewed_by = current_user.id
    pending_req.result_reason = "用户取消审核"

    dataset.dataset_status = pending_req.pre_review_status or "draft"
    dataset.status_reason = None
    print("Done")

except Exception as e:
    traceback.print_exc()
finally:
    db.close()
