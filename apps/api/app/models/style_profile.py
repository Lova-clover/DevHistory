import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class StyleProfile(Base):
    __tablename__ = "style_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=False)
    language = Column(String, nullable=False, default="ko")  # 'ko', 'en'
    tone = Column(String, nullable=False, default="technical")  # 'technical', 'casual', 'study-note'
    blog_structure = Column(JSONB, nullable=False, default=list)  # ['Intro','Problem','Approach','Result','Next']
    report_structure = Column(JSONB, nullable=False, default=list)  # ['Summary','What I did','Learned','Next']
    extra_instructions = Column(Text)  # Additional instructions for LLM
    learned_style_prompt = Column(Text)  # Auto-learned writing style from Velog posts
    learned_at = Column(DateTime(timezone=True))  # When style was last learned
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="style_profile")
