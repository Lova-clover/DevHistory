import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class GeneratedContent(Base):
    __tablename__ = "generated_contents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)  # 'weekly_blog', 'repo_blog', 'portfolio_section'
    source_ref = Column(String)  # 'weekly:{id}', 'repo:{id}'
    title = Column(String)
    content = Column(Text, nullable=False)  # Markdown or plain text
    content_metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="generated_contents")
