import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class Commit(Base):
    __tablename__ = "commits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    repo_id = Column(UUID(as_uuid=True), ForeignKey("repos.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    sha = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    committed_at = Column(DateTime(timezone=True), nullable=False)
    additions = Column(Integer)
    deletions = Column(Integer)
    files_changed = Column(Integer)
    raw_data = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    repo = relationship("Repo", back_populates="commits")
    user = relationship("User", back_populates="commits")
