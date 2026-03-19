from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class UpvoteResponse(BaseModel):
    dataset_id: UUID4
    upvote_count: int
    is_upvoted: bool = False

    class Config:
        from_attributes = True

class DiscussionCreate(BaseModel):
    content: str
    parent_id: Optional[UUID4] = None
    root_id: Optional[UUID4] = None

class DiscussionResponse(BaseModel):
    id: UUID4
    dataset_id: UUID4
    user_id: UUID4
    parent_id: Optional[UUID4] = None
    root_id: Optional[UUID4] = None
    content: str
    created_at: datetime
    updated_at: datetime
    edited_at: Optional[datetime] = None

    class Config:
        from_attributes = True
