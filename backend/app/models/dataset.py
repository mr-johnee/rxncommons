from sqlalchemy import Column, String, Text, Integer, BigInteger, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    slug = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    source_type = Column(String(50))
    source_ref = Column(String(500))
    license = Column(String(100))
    dataset_status = Column(String(30), default='draft')
    pre_archive_status = Column(String(30))
    status_reason = Column(Text)
    status_updated_at = Column(DateTime, default=func.now())
    publish_requested_at = Column(DateTime)
    current_version = Column(Integer, default=1)
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    upvote_count = Column(Integer, default=0)
    cover_image_key = Column(String(500))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    owner = relationship("User", foreign_keys=[owner_id], lazy="joined")

    __table_args__ = (
        Index('uniq_dataset_slug_active', 'owner_id', 'slug', unique=True, postgresql_where='deleted_at IS NULL'),
        Index('idx_datasets_dataset_status', 'dataset_status'),
    )

class DatasetTag(Base):
    __tablename__ = "dataset_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    tag_type = Column(String(20), nullable=False)  # 'task', 'field', 'custom'
    tag = Column(String(100), nullable=False)

    __table_args__ = (
        UniqueConstraint('dataset_id', 'tag', name='uq_dataset_tag'),
        Index('idx_dataset_tags_tag', 'tag'),
    )

class DatasetAuthor(Base):
    __tablename__ = "dataset_authors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    author_name = Column(String(255), nullable=False)
    affiliation = Column(String(255))
    orcid = Column(String(50))
    list_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())

class DatasetVersion(Base):
    __tablename__ = "dataset_versions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    version_num = Column(Integer, nullable=False)
    base_version_num = Column(Integer)
    status = Column(String(20), default='draft')
    version_note = Column(Text)
    change_manifest = Column(JSONB, default=lambda: {})
    archive_key = Column(String(500))
    download_count = Column(Integer, default=0)
    metadata_complete = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('dataset_id', 'version_num', name='uq_dataset_version'),
    )

class DatasetFile(Base):
    __tablename__ = "dataset_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    version_id = Column(UUID(as_uuid=True), ForeignKey("dataset_versions.id", ondelete="CASCADE"), nullable=False)
    file_key = Column(String(500), ForeignKey("physical_storage_objects.file_key"), nullable=False)
    filename = Column(String(255), nullable=False)
    description = Column(Text)
    row_count = Column(Integer)
    file_size = Column(BigInteger)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('version_id', 'filename', name='uq_version_filename'),
    )

class FileColumn(Base):
    __tablename__ = "file_columns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(UUID(as_uuid=True), ForeignKey("dataset_files.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    column_name = Column(String(255), nullable=False)
    column_type = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())