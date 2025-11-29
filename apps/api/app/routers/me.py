from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.models.user import User
from pydantic import BaseModel

router = APIRouter()


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    avatar_url: str | None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user


@router.get("/connections")
async def get_connections(current_user: User = Depends(get_current_user)):
    """Get user's connected accounts status."""
    return {
        "github": len([acc for acc in current_user.oauth_accounts if acc.provider == "github"]) > 0,
        "solvedac": current_user.user_profile.solvedac_handle if current_user.user_profile else None,
        "velog": current_user.user_profile.velog_id if current_user.user_profile else None,
    }
