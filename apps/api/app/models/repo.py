import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class Repo(Base):
    __tablename__ = "repos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    provider_repo_id = Column(String, nullable=False)
    full_name = Column(String, nullable=False)  # 'Lova-clover/FreshGuard'
    html_url = Column(String, nullable=False)
    description = Column(Text)
    language = Column(String)
    stars = Column(Integer, nullable=False, default=0)
    watchers = Column(Integer, nullable=False, default=0)
    forks = Column(Integer, nullable=False, default=0)
    is_fork = Column(Boolean, nullable=False, default=False)
    last_synced_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="repos")
    commits = relationship("Commit", back_populates="repo", cascade="all, delete-orphan")
