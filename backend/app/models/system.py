from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Index, Integer
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(50), nullable=False)
    target_id = Column(UUID(as_uuid=True))
    title = Column(String(255), nullable=False)
    content = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_notifications_recipient', 'recipient_id', 'is_read', 'created_at'),
    )

class DatasetSearchDocument(Base):
    __tablename__ = "dataset_search_documents"
    
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), primary_key=True)
    title_normalized = Column(Text)
    searchable_text = Column(Text)
    dataset_status = Column(String(30))
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index('idx_dataset_search_documents_status', 'dataset_status'),
        Index('idx_dataset_search_documents_title_trgm', 'title_normalized', postgresql_using='gin', postgresql_ops={'title_normalized': 'gin_trgm_ops'}),
        Index('idx_dataset_search_documents_text_trgm', 'searchable_text', postgresql_using='gin', postgresql_ops={'searchable_text': 'gin_trgm_ops'}),
    )

class AuthRefreshToken(Base):
    __tablename__ = "auth_refresh_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    user_agent = Column(String(500))

class SecurityAuditLog(Base):
    __tablename__ = "security_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    event_type = Column(String(50), nullable=False)
    ip_address = Column(String(45))
    details = Column(Text)
    created_at = Column(DateTime, default=func.now())

    __table_args__ = (
        Index('idx_security_audit_logs_event_type', 'event_type'),
        Index('idx_security_audit_logs_created_at', 'created_at'),
    )


class HomeFeaturedDataset(Base):
    __tablename__ = "home_featured_datasets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, unique=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime, default=func.now())