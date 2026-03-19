from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

# Shared properties
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    institution: Optional[str] = None
    research_area: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

# Login Schema
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Properties to return via API
class UserResponse(UserBase):
    id: UUID
    role: str
    is_active: bool
    is_email_verified: bool
    storage_used: int
    storage_quota: int
    created_at: datetime
    
    class Config:
        from_attributes = True