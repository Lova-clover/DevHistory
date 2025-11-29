"""
Profile related schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_repos: int = Field(..., ge=0)
    total_commits: int = Field(..., ge=0)
    total_problems_solved: int = Field(..., ge=0)
    total_blog_posts: int = Field(..., ge=0)
    commits_this_week: int = Field(..., ge=0)
    commits_this_month: int = Field(..., ge=0)
    problems_this_week: int = Field(..., ge=0)
    problems_this_month: int = Field(..., ge=0)
    current_streak: int = Field(..., ge=0, description="Current consecutive days of activity")
    longest_streak: int = Field(..., ge=0, description="Longest streak in days")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_repos": 25,
                "total_commits": 1234,
                "total_problems_solved": 156,
                "total_blog_posts": 23,
                "commits_this_week": 15,
                "commits_this_month": 67,
                "problems_this_week": 5,
                "problems_this_month": 18,
                "current_streak": 7,
                "longest_streak": 21
            }
        }


class ActivityTimeline(BaseModel):
    """Activity timeline entry"""
    date: datetime
    activity_type: str = Field(..., description="Type of activity (commit, problem, blog)")
    title: str
    description: Optional[str]
    metadata: Optional[dict] = Field(default=None, description="Additional activity data")
    
    class Config:
        from_attributes = True


class ActivityTimelineResponse(BaseModel):
    """Activity timeline response"""
    activities: list[ActivityTimeline]
    total: int = Field(..., ge=0)
    start_date: datetime
    end_date: datetime


class PortfolioData(BaseModel):
    """Portfolio data"""
    user_info: dict
    stats: DashboardStats
    top_repos: list[dict] = Field(..., max_length=5)
    recent_activities: list[ActivityTimeline] = Field(..., max_length=10)
    skills: list[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_info": {
                    "name": "Developer",
                    "bio": "Full-stack developer",
                    "github": "devuser",
                    "blog": "https://velog.io/@devuser"
                },
                "stats": {},
                "top_repos": [],
                "recent_activities": [],
                "skills": ["Python", "TypeScript", "React", "FastAPI"]
            }
        }


class NotificationPreference(BaseModel):
    """Notification preference settings"""
    email_weekly_summary: bool = Field(default=True)
    email_content_generated: bool = Field(default=True)
    email_sync_failures: bool = Field(default=True)
    push_enabled: bool = Field(default=False)


class PrivacySettings(BaseModel):
    """Privacy settings"""
    profile_public: bool = Field(default=True)
    show_github_stats: bool = Field(default=True)
    show_solvedac_stats: bool = Field(default=True)
    show_blog_posts: bool = Field(default=True)


class UserSettings(BaseModel):
    """User settings"""
    notifications: NotificationPreference = Field(default_factory=NotificationPreference)
    privacy: PrivacySettings = Field(default_factory=PrivacySettings)
    timezone: str = Field(default="UTC", description="User timezone")
    language: str = Field(default="ko", description="Preferred language")
    
    @field_validator('timezone')
    @classmethod
    def validate_timezone(cls, v):
        # Basic validation - can be extended with pytz
        if not v:
            return "UTC"
        return v
    
    @field_validator('language')
    @classmethod
    def validate_language(cls, v):
        allowed = ['ko', 'en']
        if v not in allowed:
            raise ValueError(f'Language must be one of {allowed}')
        return v
