from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class NotificationResponse(BaseModel):
    id: UUID
    recipient_id: UUID
    event_type: str
    target_id: Optional[UUID] = None
    title: str
    content: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        orm_mode = True
