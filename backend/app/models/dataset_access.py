from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

ACCESS_LEVEL_PUBLIC = "public"
ACCESS_LEVEL_PASSWORD_PROTECTED = "password_protected"


class DatasetAccessPolicy(Base):
    __tablename__ = "dataset_access_policies"

    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True)
    access_level = Column(String(30), nullable=False, default=ACCESS_LEVEL_PUBLIC)
    password_hash = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_dataset_access_policies_level", "access_level"),
    )
