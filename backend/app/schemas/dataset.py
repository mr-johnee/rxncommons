from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

# Shared properties
class DatasetBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field("", max_length=500)
    source_type: Optional[str] = None
    source_ref: Optional[str] = Field(None, max_length=500)
    license: Optional[str] = None

# Properties to receive on dataset creation
class DatasetCreate(DatasetBase):
    pass

class OwnerBrief(BaseModel):
    id: UUID
    username: str
    institution: Optional[str] = None
    class Config:
        from_attributes = True

# Properties to return to client
class DatasetResponse(DatasetBase):
    id: UUID
    owner_id: UUID
    slug: str
    dataset_status: str
    status_reason: Optional[str] = None
    current_version: int
    view_count: int
    download_count: int
    upvote_count: int
    total_rows: int = 0
    created_at: datetime
    updated_at: datetime
    latest_review_submitted_at: Optional[datetime] = None
    latest_reviewed_at: Optional[datetime] = None
    latest_approved_at: Optional[datetime] = None
    access_level: str = "public"
    is_password_protected: bool = False
    access_password: Optional[str] = None
    cover_image_key: Optional[str] = None
    latest_editable_version_num: Optional[int] = None
    latest_editable_version_status: Optional[str] = None
    has_published_version: bool = False
    owner: Optional[OwnerBrief] = None
    
    class Config:
        from_attributes = True

class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]
    total: int

class DatasetUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=500)
    source_type: Optional[str] = None
    source_ref: Optional[str] = Field(None, max_length=500)
    license: Optional[str] = None
