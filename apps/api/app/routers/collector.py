from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.repo import Repo
from app.models.problem import Problem
from app.models.blog_post import BlogPost
from sqlalchemy import func

router = APIRouter()


@router.post("/trigger/github")
async def trigger_github_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger manual GitHub sync."""
    from worker.tasks.sync_github import sync_github_for_user
    sync_github_for_user.delay(str(current_user.id))
    
    return {"message": "GitHub sync triggered", "status": "queued"}


@router.post("/trigger/solvedac")
async def trigger_solvedac_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger manual solved.ac sync."""
    from worker.tasks.sync_solvedac import sync_solvedac_for_user
    sync_solvedac_for_user.delay(str(current_user.id))
    
    return {"message": "solved.ac sync triggered", "status": "queued"}


@router.post("/trigger/velog")
async def trigger_velog_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger manual Velog sync."""
    from worker.tasks.sync_velog import sync_velog_for_user
    sync_velog_for_user.delay(str(current_user.id))
    
    return {"message": "Velog sync triggered", "status": "queued"}


@router.get("/status")
async def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync status for all sources."""
    # Get last sync times from database
    last_repo = db.query(Repo).filter(
        Repo.user_id == current_user.id
    ).order_by(Repo.last_synced_at.desc()).first()
    
    last_problem = db.query(Problem).filter(
        Problem.user_id == current_user.id
    ).order_by(Problem.created_at.desc()).first()
    
    last_post = db.query(BlogPost).filter(
        BlogPost.user_id == current_user.id
    ).order_by(BlogPost.created_at.desc()).first()
    
    return {
        "github": {
            "status": "idle",
            "last_synced": last_repo.last_synced_at.isoformat() if last_repo and last_repo.last_synced_at else None,
            "total_repos": db.query(func.count(Repo.id)).filter(Repo.user_id == current_user.id).scalar()
        },
        "solvedac": {
            "status": "idle",
            "last_synced": last_problem.created_at.isoformat() if last_problem else None,
            "total_problems": db.query(func.count(Problem.id)).filter(Problem.user_id == current_user.id).scalar()
        },
        "velog": {
            "status": "idle",
            "last_synced": last_post.created_at.isoformat() if last_post else None,
            "total_posts": db.query(func.count(BlogPost.id)).filter(BlogPost.user_id == current_user.id).scalar()
        },
    }
