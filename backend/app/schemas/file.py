from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class FileUploadResponse(BaseModel):
    id: UUID4
    dataset_id: UUID4
    version_id: UUID4
    filename: str
    file_size: int
    upload_status: str

    class Config:
        from_attributes = True

