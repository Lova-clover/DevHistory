import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    solvedac_handle = Column(String)
    velog_id = Column(String)
    
    # Portfolio settings
    portfolio_email = Column(String)
    portfolio_name = Column(String)
    portfolio_bio = Column(Text)
    max_portfolio_repos = Column(Integer, default=6)
    
    # Public sharing
    public_slug = Column(String, unique=True, nullable=True, index=True)
    portfolio_public = Column(Boolean, nullable=False, server_default="false")
    portfolio_show_email = Column(Boolean, nullable=False, server_default="false")
    share_token = Column(String, unique=True, nullable=True, index=True)
    share_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    public_updated_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_profile")
