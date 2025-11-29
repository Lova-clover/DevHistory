"""
Repository related schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime


class RepoResponse(BaseModel):
    """Repository response"""
    id: int
    user_id: int
    name: str = Field(..., min_length=1, description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    description: Optional[str]
    language: Optional[str]
    stars: int = Field(default=0, ge=0)
    forks: int = Field(default=0, ge=0)
    is_private: bool = Field(default=False)
    created_at: datetime
    updated_at: datetime
    last_commit_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class RepoListResponse(BaseModel):
    """Repository list response"""
    repos: list[RepoResponse]
    total: int = Field(..., ge=0)
    page: int = Field(..., gt=0)
    page_size: int = Field(..., gt=0)


class CommitResponse(BaseModel):
    """Commit response"""
    id: int
    repo_id: int
    sha: str = Field(..., min_length=40, max_length=40)
    message: str
    author_name: str
    author_email: str
    committed_at: datetime
    files_changed: int = Field(default=0, ge=0)
    additions: int = Field(default=0, ge=0)
    deletions: int = Field(default=0, ge=0)
    
    class Config:
        from_attributes = True


class CommitListResponse(BaseModel):
    """Commit list response"""
    commits: list[CommitResponse]
    total: int = Field(..., ge=0)
    repo_name: str
    page: int = Field(..., gt=0)
    page_size: int = Field(..., gt=0)


class RepoStatsResponse(BaseModel):
    """Repository statistics"""
    total_repos: int = Field(..., ge=0)
    total_commits: int = Field(..., ge=0)
    total_stars: int = Field(..., ge=0)
    total_forks: int = Field(..., ge=0)
    languages: dict[str, int] = Field(default_factory=dict, description="Language usage statistics")
    commit_frequency: dict[str, int] = Field(default_factory=dict, description="Commits per month")
    most_active_repo: Optional[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_repos": 25,
                "total_commits": 1234,
                "total_stars": 56,
                "total_forks": 12,
                "languages": {"Python": 45, "TypeScript": 30, "JavaScript": 25},
                "commit_frequency": {"2024-01": 45, "2024-02": 67, "2024-03": 89},
                "most_active_repo": "myproject"
            }
        }


class RepoDetailRequest(BaseModel):
    """Repository detail request"""
    repo_id: int = Field(..., gt=0, description="Repository ID")


class CommitFilterRequest(BaseModel):
    """Commit filter request"""
    repo_id: Optional[int] = Field(None, gt=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    author: Optional[str] = Field(None, min_length=1)
    page: int = Field(default=1, gt=0)
    page_size: int = Field(default=20, gt=0, le=100)
    
    @field_validator('page_size')
    @classmethod
    def validate_page_size(cls, v):
        if v > 100:
            raise ValueError('Page size cannot exceed 100')
        return v
    
    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        if v is not None and 'start_date' in info.data:
            start_date = info.data.get('start_date')
            if start_date and v < start_date:
                raise ValueError('End date must be after start date')
        return v
