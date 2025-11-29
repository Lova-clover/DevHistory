"""
Weekly summary related schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime, date


class WeeklySummaryCreate(BaseModel):
    """Weekly summary creation request"""
    start_date: date = Field(..., description="Week start date (Monday)")
    end_date: date = Field(..., description="Week end date (Sunday)")
    regenerate: bool = Field(default=False, description="Regenerate if already exists")
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if 'start_date' in info.data:
            start_date = info.data['start_date']
            if v <= start_date:
                raise ValueError('End date must be after start date')
            days_diff = (v - start_date).days
            if days_diff != 6:
                raise ValueError('Week must span exactly 7 days (Monday to Sunday)')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-01-07",
                "regenerate": False
            }
        }


class WeeklySummaryResponse(BaseModel):
    """Weekly summary response"""
    id: int
    user_id: int
    start_date: date
    end_date: date
    summary_text: str
    highlights: Optional[list[str]]
    commit_count: int = Field(ge=0)
    problem_count: int = Field(ge=0)
    blog_count: int = Field(ge=0)
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WeeklySummaryListResponse(BaseModel):
    """Weekly summary list response"""
    summaries: list[WeeklySummaryResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., gt=0)
    page_size: int = Field(..., gt=0)


class WeeklySummaryStats(BaseModel):
    """Weekly summary statistics"""
    total_summaries: int = Field(..., ge=0)
    total_commits: int = Field(..., ge=0)
    total_problems: int = Field(..., ge=0)
    total_blogs: int = Field(..., ge=0)
    average_commits_per_week: float = Field(..., ge=0)
    most_productive_week: Optional[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_summaries": 12,
                "total_commits": 234,
                "total_problems": 45,
                "total_blogs": 8,
                "average_commits_per_week": 19.5,
                "most_productive_week": "2024-01-15"
            }
        }


class WeeklyFilterRequest(BaseModel):
    """Weekly summary filter request"""
    year: Optional[int] = Field(None, ge=2020, le=2100)
    month: Optional[int] = Field(None, ge=1, le=12)
    page: int = Field(default=1, gt=0)
    page_size: int = Field(default=10, gt=0, le=50)
    
    @field_validator('page_size')
    @classmethod
    def validate_page_size(cls, v):
        if v > 50:
            raise ValueError('Page size cannot exceed 50')
        return v
