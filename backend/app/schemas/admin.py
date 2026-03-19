from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.schemas.dataset import OwnerBrief

class ReviewRejectReq(BaseModel):
    result_reason: str

class SuggestionCreate(BaseModel):
    suggestion_text: str

class DatasetBrief(BaseModel):
    id: UUID
    title: str
    dataset_status: Optional[str] = None
    access_level: Optional[str] = "public"
    is_password_protected: Optional[bool] = False
    owner: Optional[OwnerBrief] = None
    class Config:
        from_attributes = True

class ReviewRequestResponse(BaseModel):
    id: UUID
    dataset_id: UUID
    version_id: Optional[UUID] = None
    version_num: Optional[int] = None
    submitted_by: UUID
    status: str
    pre_review_status: Optional[str] = None
    submitted_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[UUID] = None
    rejection_reason: Optional[str] = None
    dataset: Optional[DatasetBrief] = None
    
    class Config:
        from_attributes = True


class ReviewRequestListResponse(BaseModel):
    items: List[ReviewRequestResponse]
    total: int
    status_counts: dict[str, int]

class UserAdminUpdateBase(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None

class UserQuotaUpdate(BaseModel):
    quota_bytes: int
