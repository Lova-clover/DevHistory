from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.style_profile import StyleProfile
from pydantic import BaseModel

router = APIRouter()


class UserProfileUpdate(BaseModel):
    solvedac_handle: str | None = None
    velog_id: str | None = None


class StyleProfileUpdate(BaseModel):
    language: str = "ko"
    tone: str = "technical"
    blog_structure: list[str] = ["Intro", "Problem", "Approach", "Result", "Next"]
    report_structure: list[str] = ["Summary", "What I did", "Learned", "Next"]
    extra_instructions: str | None = None


@router.get("/user")
async def get_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user profile (solved.ac, velog)."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        return {"solvedac_handle": None, "velog_id": None}
    
    return {
        "solvedac_handle": profile.solvedac_handle,
        "velog_id": profile.velog_id,
    }


@router.put("/user")
async def update_user_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
    
    if data.solvedac_handle is not None:
        profile.solvedac_handle = data.solvedac_handle
    if data.velog_id is not None:
        profile.velog_id = data.velog_id
    
    db.commit()
    db.refresh(profile)
    
    return {
        "solvedac_handle": profile.solvedac_handle,
        "velog_id": profile.velog_id,
    }


@router.get("/style")
async def get_style_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get style profile."""
    style = db.query(StyleProfile).filter(StyleProfile.user_id == current_user.id).first()
    if not style:
        return {
            "language": "ko",
            "tone": "technical",
            "blog_structure": ["Intro", "Problem", "Approach", "Result", "Next"],
            "report_structure": ["Summary", "What I did", "Learned", "Next"],
            "extra_instructions": None,
        }
    
    return {
        "language": style.language,
        "tone": style.tone,
        "blog_structure": style.blog_structure,
        "report_structure": style.report_structure,
        "extra_instructions": style.extra_instructions,
    }


@router.put("/style")
async def update_style_profile(
    data: StyleProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update style profile."""
    style = db.query(StyleProfile).filter(StyleProfile.user_id == current_user.id).first()
    if not style:
        style = StyleProfile(
            user_id=current_user.id,
            language=data.language,
            tone=data.tone,
            blog_structure=data.blog_structure,
            report_structure=data.report_structure,
            extra_instructions=data.extra_instructions,
        )
        db.add(style)
    else:
        style.language = data.language
        style.tone = data.tone
        style.blog_structure = data.blog_structure
        style.report_structure = data.report_structure
        style.extra_instructions = data.extra_instructions
    
    db.commit()
    db.refresh(style)
    
    return {
        "language": style.language,
        "tone": style.tone,
        "blog_structure": style.blog_structure,
        "report_structure": style.report_structure,
        "extra_instructions": style.extra_instructions,
    }
