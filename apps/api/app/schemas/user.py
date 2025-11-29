"""
User related schemas
"""
from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional
from datetime import datetime


class UserProfileUpdate(BaseModel):
    """User profile update request"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Display name")
    bio: Optional[str] = Field(None, max_length=500, description="User biography")
    blog_url: Optional[str] = Field(None, max_length=200, description="Blog URL")
    linkedin_url: Optional[str] = Field(None, max_length=200, description="LinkedIn URL")
    
    @field_validator('display_name', 'bio', 'blog_url', 'linkedin_url')
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @field_validator('blog_url', 'linkedin_url')
    @classmethod
    def validate_url(cls, v):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v


class UserProfileResponse(BaseModel):
    """User profile response"""
    id: int
    user_id: int
    display_name: Optional[str]
    bio: Optional[str]
    blog_url: Optional[str]
    linkedin_url: Optional[str]
    github_stats_public: bool = True
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StyleProfileUpdate(BaseModel):
    """Style profile update request"""
    tone: Optional[str] = Field(None, description="Writing tone (e.g., professional, casual, technical)")
    style: Optional[str] = Field(None, description="Writing style preferences")
    focus_areas: Optional[list[str]] = Field(None, max_length=10, description="Focus areas")
    
    @field_validator('focus_areas')
    @classmethod
    def validate_focus_areas(cls, v):
        if v is not None:
            # Remove empty strings and duplicates
            cleaned = list(set(item.strip() for item in v if item.strip()))
            if len(cleaned) > 10:
                raise ValueError('Maximum 10 focus areas allowed')
            return cleaned
        return v


class StyleProfileResponse(BaseModel):
    """Style profile response"""
    id: int
    user_id: int
    tone: Optional[str]
    style: Optional[str]
    focus_areas: Optional[list[str]]
    sample_content: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
