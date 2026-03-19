from sqlalchemy import Column, String, Boolean, BigInteger, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    institution = Column(String(255))
    research_area = Column(String(255))
    role = Column(String(20), default='user')  # 'user' | 'admin'
    storage_used = Column(BigInteger, default=0)
    storage_quota = Column(BigInteger, default=5368709120)  # Default 5GB
    is_active = Column(Boolean, default=True)
    is_email_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)