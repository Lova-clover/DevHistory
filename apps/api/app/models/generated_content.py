import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


class GeneratedContent(Base):
    __tablename__ = "generated_contents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    content_type = Column(String, nullable=False)  # 'weekly_blog', 'repo_blog', 'portfolio_section', 'blog_post', 'summary', 'report'
    source_ref = Column(String, nullable=True)  # 'weekly:{id}', 'repo:{id}'
    title = Column(String)
    content = Column(Text, nullable=False, server_default="")
    # SQLAlchemy Declarative reserves the attribute name "metadata".
    # Keep DB column name as "metadata" while using a safe Python attribute.
    content_metadata = Column("metadata", JSONB, nullable=True)
    status = Column(String, nullable=False, server_default="completed")  # pending, generating, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    generation_seconds = Column(Float, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="generated_contents")
