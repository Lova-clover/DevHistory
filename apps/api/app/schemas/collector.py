"""
Data collector related schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime


class SyncRequest(BaseModel):
    """Data synchronization request"""
    source: Literal["github", "solvedac", "velog"] = Field(..., description="Data source")
    force_full_sync: bool = Field(default=False, description="Force full synchronization instead of incremental")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "github",
                "force_full_sync": False
            }
        }


class SyncStatus(BaseModel):
    """Synchronization status"""
    source: str = Field(..., description="Data source")
    status: Literal["pending", "running", "completed", "failed"] = Field(..., description="Sync status")
    last_synced_at: Optional[datetime] = Field(None, description="Last successful sync time")
    items_synced: int = Field(default=0, ge=0, description="Number of items synchronized")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "github",
                "status": "completed",
                "last_synced_at": "2024-01-01T12:00:00Z",
                "items_synced": 150,
                "error_message": None
            }
        }


class CollectorConfig(BaseModel):
    """Collector configuration"""
    github_username: Optional[str] = Field(None, min_length=1, description="GitHub username")
    solvedac_username: Optional[str] = Field(None, min_length=1, description="solved.ac username")
    velog_username: Optional[str] = Field(None, min_length=1, description="Velog username")
    
    @field_validator('github_username', 'solvedac_username', 'velog_username')
    @classmethod
    def strip_and_validate(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Username cannot be empty or whitespace')
            return v
        return v


class CollectorConfigResponse(BaseModel):
    """Collector configuration response"""
    github_username: Optional[str]
    github_connected: bool = False
    solvedac_username: Optional[str]
    solvedac_connected: bool = False
    velog_username: Optional[str]
    velog_connected: bool = False
    last_github_sync: Optional[datetime]
    last_solvedac_sync: Optional[datetime]
    last_velog_sync: Optional[datetime]


# External API response schemas for validation
class GitHubCommitSchema(BaseModel):
    """GitHub commit data schema"""
    sha: str = Field(..., min_length=40, max_length=40)
    message: str = Field(..., min_length=1)
    author_name: str = Field(..., min_length=1)
    author_email: str
    committed_at: datetime
    repo_name: str = Field(..., min_length=1)
    
    @field_validator('sha')
    @classmethod
    def validate_sha(cls, v):
        if not all(c in '0123456789abcdef' for c in v.lower()):
            raise ValueError('Invalid commit SHA format')
        return v


class SolvedacProblemSchema(BaseModel):
    """solved.ac problem data schema"""
    problem_id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1)
    level: int = Field(..., ge=0, le=30)
    solved_at: datetime
    tags: Optional[list[str]] = Field(default=None)
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v):
        if v is not None:
            return [tag.strip() for tag in v if tag.strip()]
        return v


class VelogPostSchema(BaseModel):
    """Velog blog post data schema"""
    post_id: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    published_at: datetime
    tags: Optional[list[str]] = Field(default=None)
    url: str = Field(..., min_length=1)
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v
