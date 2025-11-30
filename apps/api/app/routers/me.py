from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.deps import get_current_user, get_db
from app.models.user import User
from app.models.repo import Repo
from app.models.commit import Commit
from app.models.problem import Problem
from app.models.blog_post import BlogPost
from pydantic import BaseModel
from datetime import datetime, timedelta

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


@router.get("/portfolio")
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's portfolio data aggregated from all sources."""
    
    # Get repos
    repos = db.query(Repo).filter(Repo.user_id == current_user.id).all()
    total_repos = len(repos)
    total_stars = sum(repo.stars or 0 for repo in repos)
    
    # Get commits - count directly from database
    total_commits = db.query(func.count(Commit.id)).filter(
        Commit.user_id == current_user.id
    ).scalar() or 0
    
    # Get problems
    total_problems = db.query(func.count(Problem.id)).filter(
        Problem.user_id == current_user.id
    ).scalar() or 0
    
    # Get blog posts
    total_blogs = db.query(func.count(BlogPost.id)).filter(
        BlogPost.user_id == current_user.id
    ).scalar() or 0
    
    # Language statistics
    language_stats = {}
    for repo in repos:
        if repo.language:
            language_stats[repo.language] = language_stats.get(repo.language, 0) + 1
    
    # Top languages by repository count
    language_repos = db.query(
        Repo.language,
        func.count(Repo.id).label("repo_count")
    ).filter(
        Repo.user_id == current_user.id,
        Repo.language.isnot(None)
    ).group_by(Repo.language).order_by(desc("repo_count")).limit(10).all()
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_commits = db.query(Commit).filter(
        Commit.user_id == current_user.id,
        Commit.committed_at >= thirty_days_ago
    ).count()
    
    # Calculate activity days (days with commits)
    activity_days = db.query(
        func.date(Commit.committed_at).label("date")
    ).filter(
        Commit.user_id == current_user.id
    ).distinct().count()
    
    # Top repositories by commit count
    from sqlalchemy import func as sql_func
    from app.models.user_profile import UserProfile
    
    # Get user profile settings
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    max_repos = user_profile.max_portfolio_repos if user_profile and user_profile.max_portfolio_repos else 6
    
    repo_commit_counts = db.query(
        Repo.id,
        sql_func.count(Commit.id).label('commit_count')
    ).join(Commit, Commit.repo_id == Repo.id).filter(
        Repo.user_id == current_user.id
    ).group_by(Repo.id).order_by(desc('commit_count')).limit(max_repos).all()
    
    top_repo_ids = [r.id for r in repo_commit_counts]
    top_repos = db.query(Repo).filter(Repo.id.in_(top_repo_ids)).all() if top_repo_ids else []
    # Sort by commit count order
    top_repos_dict = {repo.id: repo for repo in top_repos}
    top_repos = [top_repos_dict[repo_id] for repo_id in top_repo_ids if repo_id in top_repos_dict]
    
    # Get recent commits for activity feed
    recent_commit_list = db.query(Commit).filter(
        Commit.user_id == current_user.id
    ).order_by(desc(Commit.committed_at)).limit(10).all()
    
    # Get GitHub username from OAuth
    github_username = None
    for acc in current_user.oauth_accounts:
        if acc.provider == "github":
            # Try to extract username from provider_user_id or fetch from repos
            if repos:
                # Extract from first repo's full_name (format: username/repo)
                github_username = repos[0].full_name.split('/')[0] if '/' in repos[0].full_name else None
            break
    
    return {
        "user": {
            "id": str(current_user.id),
            "name": user_profile.portfolio_name if user_profile and user_profile.portfolio_name else current_user.name,
            "email": user_profile.portfolio_email if user_profile and user_profile.portfolio_email else current_user.email,
            "bio": user_profile.portfolio_bio if user_profile and user_profile.portfolio_bio else None,
            "avatar_url": current_user.avatar_url,
            "github_username": github_username,
        },
        "stats": {
            "total_repos": total_repos,
            "total_commits": total_commits,
            "total_problems": total_problems,
            "total_blogs": total_blogs,
            "total_stars": total_stars,
            "activity_days": activity_days,
            "recent_commits": recent_commits,
        },
        "languages": [
            {"name": lang, "count": count}
            for lang, count in language_repos
        ],
        "top_repos": [
            {
                "id": str(repo.id),
                "name": repo.full_name.split('/')[-1] if '/' in repo.full_name else repo.full_name,
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "stars": repo.stars or 0,
                "forks": repo.forks or 0,
                "html_url": repo.html_url,
            }
            for repo in top_repos
        ],
        "recent_activity": [
            {
                "id": str(commit.id),
                "type": "commit",
                "date": commit.committed_at.isoformat() if commit.committed_at else None,
                "message": commit.message,
                "repo_name": next((r.full_name for r in repos if r.id == commit.repo_id), "Unknown"),
            }
            for commit in recent_commit_list
        ]
    }
