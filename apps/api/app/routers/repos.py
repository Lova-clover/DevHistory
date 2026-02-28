from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.repo import Repo
from pydantic import BaseModel

router = APIRouter()


class RepoResponse(BaseModel):
    id: str
    full_name: str
    html_url: str
    description: str | None
    language: str | None
    stars: int
    forks: int
    is_fork: bool
    last_synced_at: str | None
    
    class Config:
        from_attributes = True


@router.get("")
@router.get("/")
async def list_repos(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all repos for current user."""
    repos = db.query(Repo).filter(
        Repo.user_id == current_user.id
    ).order_by(Repo.stars.desc()).all()
    
    return [
        {
            "id": str(repo.id),
            "name": repo.full_name.split("/")[-1] if repo.full_name else "Unknown",
            "full_name": repo.full_name,
            "html_url": repo.html_url,
            "description": repo.description,
            "language": repo.language,
            "stars": repo.stars,
            "forks": repo.forks,
            "watchers": repo.watchers,
            "is_fork": repo.is_fork,
            "last_commit_at": repo.last_synced_at.isoformat() if repo.last_synced_at else None,
            "last_synced_at": repo.last_synced_at.isoformat() if repo.last_synced_at else None,
        }
        for repo in repos
    ]


@router.get("/{repo_id}")
async def get_repo(
    repo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed repo information."""
    repo = db.query(Repo).filter(
        Repo.id == repo_id,
        Repo.user_id == current_user.id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Get recent commits
    recent_commits = [
        {
            "sha": commit.sha,
            "message": commit.message,
            "committed_at": commit.committed_at.isoformat(),
            "additions": commit.additions,
            "deletions": commit.deletions,
        }
        for commit in repo.commits[:10]  # Last 10 commits
    ]
    
    return {
        "id": str(repo.id),
        "full_name": repo.full_name,
        "html_url": repo.html_url,
        "description": repo.description,
        "language": repo.language,
        "stars": repo.stars,
        "forks": repo.forks,
        "is_fork": repo.is_fork,
        "last_synced_at": repo.last_synced_at.isoformat() if repo.last_synced_at else None,
        "recent_commits": recent_commits,
    }
