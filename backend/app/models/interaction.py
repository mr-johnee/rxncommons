from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Upvote(Base):
    __tablename__ = "upvotes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        UniqueConstraint('dataset_id', 'user_id', name='uq_upvote_dataset_user'),
    )

class Discussion(Base):
    __tablename__ = "discussions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("discussions.id"))
    root_id = Column(UUID(as_uuid=True), ForeignKey("discussions.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    edited_at = Column(DateTime)
    deleted_at = Column(DateTime)
    deleted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_discussions_root_id', 'root_id'),
    )

class AdminSuggestion(Base):
    __tablename__ = "admin_suggestions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    suggestion_text = Column(Text, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    recipient_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default='pending')
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)

    __table_args__ = (
        Index('idx_admin_suggestions_recipient_status', 'recipient_user_id', 'status', 'is_read'),
    )

class DatasetReviewRequest(Base):
    __tablename__ = "dataset_review_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(30), default='pending')
    pre_review_status = Column(String(30))
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    submitted_at = Column(DateTime, default=func.now())
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at = Column(DateTime)
    result_reason = Column(Text)

    dataset = relationship("Dataset", foreign_keys=[dataset_id], lazy="joined")

    __table_args__ = (
        # equivalent SQL: CREATE INDEX idx_review_requests_status_time ON dataset_review_requests(status, submitted_at DESC);
        Index('idx_review_requests_status_time', 'status', 'submitted_at'),
        # equivalent SQL: CREATE UNIQUE INDEX uniq_review_request_pending_per_dataset ON dataset_review_requests(dataset_id) WHERE status = 'pending';
        Index('uniq_review_request_pending_per_dataset', 'dataset_id', unique=True, postgresql_where="status = 'pending'"),
    )