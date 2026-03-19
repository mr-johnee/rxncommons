from sqlalchemy import Column, String, Integer, BigInteger, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class PhysicalStorageObject(Base):
    __tablename__ = "physical_storage_objects"
    
    file_key = Column(String(500), primary_key=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    file_size = Column(BigInteger, nullable=False)
    ref_count = Column(Integer, default=0)
    upload_status = Column(String(20), default='pending')
    created_at = Column(DateTime, default=func.now())