"""
Authentication related schemas
"""
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class OAuthCallbackRequest(BaseModel):
    """OAuth callback request"""
    code: str = Field(..., min_length=1, description="OAuth authorization code")
    state: Optional[str] = Field(None, description="OAuth state parameter")
    
    @validator('code')
    def validate_code(cls, v):
        if not v or v.isspace():
            raise ValueError('Authorization code cannot be empty')
        return v.strip()


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., gt=0, description="Token expiration time in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class UserInfo(BaseModel):
    """User information"""
    id: int = Field(..., gt=0, description="User ID")
    github_username: str = Field(..., min_length=1, description="GitHub username")
    email: Optional[str] = Field(None, description="User email")
    avatar_url: Optional[str] = Field(None, description="Avatar image URL")
    created_at: datetime = Field(..., description="Account creation time")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "github_username": "devuser",
                "email": "user@example.com",
                "avatar_url": "https://avatars.githubusercontent.com/u/12345",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
