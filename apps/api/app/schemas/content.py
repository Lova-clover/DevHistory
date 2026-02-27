"""
Content generation related schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime


class ContentGenerateRequest(BaseModel):
    """Content generation request"""
    content_type: Literal["blog_post", "portfolio", "summary", "report"] = Field(..., description="Type of content to generate")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Content title")
    context: Optional[str] = Field(None, max_length=2000, description="Additional context or instructions")
    date_range_start: Optional[datetime] = Field(None, description="Start date for data range")
    date_range_end: Optional[datetime] = Field(None, description="End date for data range")
    use_style_profile: bool = Field(default=True, description="Apply user's style profile")
    
    @field_validator('title', 'context')
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            return v.strip() if v.strip() else None
        return v
    
    @field_validator('date_range_end')
    @classmethod
    def validate_date_range(cls, v, info):
        if v is not None and 'date_range_start' in info.data:
            start = info.data.get('date_range_start')
            if start and v < start:
                raise ValueError('End date must be after start date')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "content_type": "blog_post",
                "title": "My Weekly Development Journey",
                "context": "Focus on React and TypeScript projects",
                "date_range_start": "2024-01-01T00:00:00Z",
                "date_range_end": "2024-01-07T23:59:59Z",
                "use_style_profile": True
            }
        }


class ContentResponse(BaseModel):
    """Generated content response"""
    id: str
    user_id: str
    content_type: str
    title: str
    content: str
    metadata: Optional[dict] = Field(default=None, description="Additional metadata")
    status: Literal["pending", "generating", "completed", "failed"]
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ContentListResponse(BaseModel):
    """Content list response"""
    contents: list[ContentResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., gt=0)
    page_size: int = Field(..., gt=0)


class ContentUpdateRequest(BaseModel):
    """Content update request"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    metadata: Optional[dict] = None
    
    @field_validator('title', 'content')
    @classmethod
    def strip_whitespace(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Field cannot be empty or whitespace')
            return v
        return v


class ContentRegenerateRequest(BaseModel):
    """Content regeneration request"""
    new_context: Optional[str] = Field(None, max_length=2000, description="New context for regeneration")
    use_style_profile: bool = Field(default=True)


class ContentFilterRequest(BaseModel):
    """Content filter request"""
    content_type: Optional[Literal["blog_post", "portfolio", "summary", "report"]] = None
    status: Optional[Literal["pending", "generating", "completed", "failed"]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, gt=0)
    page_size: int = Field(default=20, gt=0, le=100)
    
    @field_validator('page_size')
    @classmethod
    def validate_page_size(cls, v):
        if v > 100:
            raise ValueError('Page size cannot exceed 100')
        return v


class ContentStatsResponse(BaseModel):
    """Content generation statistics"""
    total_generated: int = Field(..., ge=0)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_status: dict[str, int] = Field(default_factory=dict)
    success_rate: float = Field(..., ge=0, le=100)
    average_generation_time: Optional[float] = Field(None, description="Average time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_generated": 45,
                "by_type": {"blog_post": 20, "portfolio": 5, "summary": 15, "report": 5},
                "by_status": {"completed": 40, "failed": 5},
                "success_rate": 88.9,
                "average_generation_time": 12.5
            }
        }
