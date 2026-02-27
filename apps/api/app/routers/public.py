"""Public portfolio endpoints – no auth required."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.repo import Repo
from app.models.commit import Commit
from app.models.problem import Problem
from app.models.blog_post import BlogPost

router = APIRouter()


def _build_public_portfolio(user: User, profile: UserProfile, db: Session, show_email: bool = False):
    """Build portfolio JSON for public/share pages."""
    repos = db.query(Repo).filter(
        Repo.user_id == user.id,
        Repo.is_fork == False,
    ).all()

    total_commits = db.query(func.count(Commit.id)).filter(Commit.user_id == user.id).scalar() or 0
    total_problems = db.query(func.count(Problem.id)).filter(Problem.user_id == user.id).scalar() or 0
    total_blogs = db.query(func.count(BlogPost.id)).filter(BlogPost.user_id == user.id).scalar() or 0

    language_repos = db.query(
        Repo.language, func.count(Repo.id).label("repo_count")
    ).filter(
        Repo.user_id == user.id, Repo.language.isnot(None), Repo.is_fork == False,
    ).group_by(Repo.language).order_by(desc("repo_count")).limit(10).all()

    max_repos = profile.max_portfolio_repos if profile.max_portfolio_repos else 6
    repo_commit_counts = db.query(
        Repo.id, func.count(Commit.id).label("cc")
    ).join(Commit, Commit.repo_id == Repo.id).filter(
        Repo.user_id == user.id, Repo.is_fork == False,
    ).group_by(Repo.id).order_by(desc("cc")).limit(max_repos).all()

    top_repo_ids = [r.id for r in repo_commit_counts]
    top_repos = db.query(Repo).filter(Repo.id.in_(top_repo_ids)).all() if top_repo_ids else []
    top_repos_dict = {r.id: r for r in top_repos}
    top_repos_sorted = [top_repos_dict[rid] for rid in top_repo_ids if rid in top_repos_dict]

    email = None
    if show_email:
        email = profile.portfolio_email or user.email

    return {
        "user": {
            "name": profile.portfolio_name or user.name,
            "email": email,
            "bio": profile.portfolio_bio,
            "avatar_url": user.avatar_url,
            "github_username": user.github_username,
        },
        "stats": {
            "total_repos": len(repos),
            "total_commits": total_commits,
            "total_problems": total_problems,
            "total_blogs": total_blogs,
            "total_stars": sum(r.stars or 0 for r in repos),
        },
        "languages": [{"name": lang, "count": cnt} for lang, cnt in language_repos],
        "top_repos": [
            {
                "name": r.full_name.split("/")[-1] if "/" in r.full_name else r.full_name,
                "full_name": r.full_name,
                "description": r.description,
                "language": r.language,
                "stars": r.stars or 0,
                "forks": r.forks or 0,
                "html_url": r.html_url,
            }
            for r in top_repos_sorted
        ],
    }


@router.get("/portfolio/{slug}")
async def get_public_portfolio(slug: str, db: Session = Depends(get_db)):
    """Public portfolio by slug – no auth required."""
    profile = db.query(UserProfile).filter(
        UserProfile.public_slug == slug,
        UserProfile.portfolio_public == True,
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    user = db.query(User).filter(User.id == profile.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return _build_public_portfolio(user, profile, db, show_email=profile.portfolio_show_email)


@router.get("/share/{token}")
async def get_shared_portfolio(token: str, db: Session = Depends(get_db)):
    """Private share link – token-based, no auth required, noindex."""
    profile = db.query(UserProfile).filter(UserProfile.share_token == token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Invalid share link")

    # Check expiry
    if profile.share_token_expires_at and profile.share_token_expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Share link has expired")

    user = db.query(User).filter(User.id == profile.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = _build_public_portfolio(user, profile, db, show_email=profile.portfolio_show_email)
    data["noindex"] = True
    return data
