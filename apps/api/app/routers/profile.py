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
    portfolio_email: str | None = None
    portfolio_name: str | None = None
    portfolio_bio: str | None = None
    max_portfolio_repos: int | None = None


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
    """Get user profile (solved.ac, velog, portfolio settings)."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        return {
            "solvedac_handle": None,
            "velog_id": None,
            "portfolio_email": None,
            "portfolio_name": None,
            "portfolio_bio": None,
            "max_portfolio_repos": 6
        }
    
    return {
        "solvedac_handle": profile.solvedac_handle,
        "velog_id": profile.velog_id,
        "portfolio_email": profile.portfolio_email,
        "portfolio_name": profile.portfolio_name,
        "portfolio_bio": profile.portfolio_bio,
        "max_portfolio_repos": profile.max_portfolio_repos or 6,
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
    if data.portfolio_email is not None:
        profile.portfolio_email = data.portfolio_email
    if data.portfolio_name is not None:
        profile.portfolio_name = data.portfolio_name
    if data.portfolio_bio is not None:
        profile.portfolio_bio = data.portfolio_bio
    if data.max_portfolio_repos is not None:
        profile.max_portfolio_repos = data.max_portfolio_repos
    
    db.commit()
    db.refresh(profile)
    
    return {
        "solvedac_handle": profile.solvedac_handle,
        "velog_id": profile.velog_id,
        "portfolio_email": profile.portfolio_email,
        "portfolio_name": profile.portfolio_name,
        "portfolio_bio": profile.portfolio_bio,
        "max_portfolio_repos": profile.max_portfolio_repos or 6,
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
        "learned_style_prompt": style.learned_style_prompt,
        "learned_at": style.learned_at.isoformat() if style.learned_at else None,
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
        "learned_style_prompt": style.learned_style_prompt,
        "learned_at": style.learned_at.isoformat() if style.learned_at else None,
    }


class LearnedStyleUpdate(BaseModel):
    learned_style_prompt: str


@router.post("/style/learn")
async def learn_writing_style(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger Velog style analysis. Returns immediately — analysis runs in background."""
    from app.models.user_profile import UserProfile as UP
    profile = db.query(UP).filter(UP.user_id == current_user.id).first()
    if not profile or not profile.velog_id:
        from fastapi import HTTPException
        raise HTTPException(400, "Velog ID를 먼저 설정해주세요")

    from worker.tasks.forge_llm import learn_velog_style
    task = learn_velog_style.delay(str(current_user.id))

    # Wait for result with timeout  
    import time
    max_wait = 30
    start = time.time()
    while time.time() - start < max_wait:
        if task.ready():
            result = task.get()
            if result.get("status") == "success":
                return {"status": "success", "learned_style_prompt": result.get("learned_prompt")}
            return {"status": "error", "error": result.get("error", "Unknown error")}
        time.sleep(0.5)

    return {"status": "processing", "message": "스타일 분석이 진행 중입니다. 잠시 후 다시 확인해주세요."}


@router.put("/style/learned-prompt")
async def update_learned_prompt(
    data: LearnedStyleUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update the learned style prompt (user can edit it)."""
    style = db.query(StyleProfile).filter(StyleProfile.user_id == current_user.id).first()
    if not style:
        style = StyleProfile(
            user_id=current_user.id,
            language="ko",
            tone="technical",
            blog_structure=["Intro", "Problem", "Approach", "Result", "Next"],
            report_structure=["Summary", "What I did", "Learned", "Next"],
        )
        db.add(style)
    
    style.learned_style_prompt = data.learned_style_prompt
    db.commit()
    db.refresh(style)
    
    return {"learned_style_prompt": style.learned_style_prompt}
