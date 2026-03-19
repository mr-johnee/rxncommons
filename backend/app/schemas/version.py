from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, Any

class VersionResponse(BaseModel):
    id: UUID4
    dataset_id: UUID4
    version_num: int
    status: str
    version_note: Optional[str] = None
    base_version_num: Optional[int] = None
    download_count: int
    metadata_complete: bool
    change_manifest: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True

class VersionCreateItem(BaseModel):
    base_version_num: Optional[int] = None
    reset_existing_draft: bool = False
