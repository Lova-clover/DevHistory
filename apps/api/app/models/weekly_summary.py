import uuid
from datetime import datetime, date
from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Date, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class WeeklySummary(Base):
    __tablename__ = "weekly_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    week_start = Column(Date, nullable=False)  # Monday
    week_end = Column(Date, nullable=False)  # Sunday
    commit_count = Column(Integer, nullable=False, default=0)
    problem_count = Column(Integer, nullable=False, default=0)
    note_count = Column(Integer, nullable=False, default=0)
    summary_json = Column(JSONB, nullable=False, default=dict)  # Graph data
    llm_summary = Column(Text)  # Generated markdown content
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="weekly_summaries")
