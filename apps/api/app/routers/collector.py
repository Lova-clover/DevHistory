from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.repo import Repo
from app.models.problem import Problem
from app.models.blog_post import BlogPost
from app.models.user_profile import UserProfile
from app.schemas.collector import (
    SyncRequest, 
    SyncStatus, 
    CollectorConfig,
    CollectorConfigResponse
)
from sqlalchemy import func
from datetime import datetime
from typing import Optional

router = APIRouter()


def _is_sync_task_running(source: str, user_id: str) -> bool:
    """Best-effort check whether a source sync task is queued/running for this user."""
    task_suffix = {
        "github": "sync_github_for_user",
        "solvedac": "sync_solvedac_for_user",
        "velog": "sync_velog_for_user",
    }[source]

    try:
        from worker.celery_app import celery_app

        inspector = celery_app.control.inspect(timeout=0.5)
        task_sets = [
            inspector.active() or {},
            inspector.reserved() or {},
            inspector.scheduled() or {},
        ]
        for tasks_by_worker in task_sets:
            for tasks in tasks_by_worker.values():
                for task in tasks:
                    name = str(task.get("name", ""))
                    if not name.endswith(task_suffix):
                        continue
                    args_repr = str(task.get("args", ""))
                    kwargs_repr = str(task.get("kwargs", ""))
                    if user_id in args_repr or user_id in kwargs_repr:
                        return True
    except Exception:
        return False

    return False


@router.post("/sync", response_model=SyncStatus)
async def trigger_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger data synchronization from specified source."""
    task_map = {
        "github": ("worker.tasks.sync_github", "sync_github_for_user"),
        "solvedac": ("worker.tasks.sync_solvedac", "sync_solvedac_for_user"),
        "velog": ("worker.tasks.sync_velog", "sync_velog_for_user")
    }
    
    module_name, func_name = task_map[request.source]
    module = __import__(module_name, fromlist=[func_name])
    task_func = getattr(module, func_name)
    
    task = task_func.delay(str(current_user.id))
    
    # Get last sync time
    last_synced = None
    if request.source == "github":
        last_synced = db.query(func.max(Repo.updated_at)).filter(Repo.user_id == current_user.id).scalar()
    elif request.source == "solvedac":
        last_synced = db.query(func.max(Problem.created_at)).filter(Problem.user_id == current_user.id).scalar()
    elif request.source == "velog":
        last_synced = db.query(func.max(BlogPost.created_at)).filter(BlogPost.user_id == current_user.id).scalar()
    
    return SyncStatus(
        source=request.source,
        status="pending",
        last_synced_at=last_synced,
        items_synced=0
    )


@router.post("/trigger/github", deprecated=True)
async def trigger_github_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger manual GitHub sync. (Deprecated: Use /sync endpoint)"""
    from worker.tasks.sync_github import sync_github_for_user
    sync_github_for_user.delay(str(current_user.id))
    
    return {"message": "GitHub sync triggered", "status": "queued"}


@router.post("/trigger/solvedac", deprecated=True)
async def trigger_solvedac_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger manual solved.ac sync. (Deprecated: Use /sync endpoint)"""
    from worker.tasks.sync_solvedac import sync_solvedac_for_user
    sync_solvedac_for_user.delay(str(current_user.id))
    
    return {"message": "solved.ac sync triggered", "status": "queued"}


@router.post("/trigger/velog", deprecated=True)
async def trigger_velog_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger manual Velog sync. (Deprecated: Use /sync endpoint)"""
    from worker.tasks.sync_velog import sync_velog_for_user
    sync_velog_for_user.delay(str(current_user.id))
    
    return {"message": "Velog sync triggered", "status": "queued"}


@router.get("/status", response_model=list[SyncStatus])
async def get_sync_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sync status for all sources."""
    # Get last sync times and counts from database
    last_repo = db.query(Repo).filter(
        Repo.user_id == current_user.id
    ).order_by(Repo.last_synced_at.desc()).first()
    
    last_problem = db.query(Problem).filter(
        Problem.user_id == current_user.id
    ).order_by(Problem.created_at.desc()).first()
    
    last_post = db.query(BlogPost).filter(
        BlogPost.user_id == current_user.id
    ).order_by(BlogPost.created_at.desc()).first()
    
    github_count = db.query(func.count(Repo.id)).filter(Repo.user_id == current_user.id).scalar() or 0
    problem_count = db.query(func.count(Problem.id)).filter(Problem.user_id == current_user.id).scalar() or 0
    post_count = db.query(func.count(BlogPost.id)).filter(BlogPost.user_id == current_user.id).scalar() or 0
    
    user_id = str(current_user.id)
    github_running = _is_sync_task_running("github", user_id)
    solvedac_running = _is_sync_task_running("solvedac", user_id)
    velog_running = _is_sync_task_running("velog", user_id)

    return [
        SyncStatus(
            source="github",
            status="running" if github_running else ("completed" if github_count > 0 else "pending"),
            last_synced_at=last_repo.last_synced_at if last_repo and last_repo.last_synced_at else None,
            items_synced=github_count
        ),
        SyncStatus(
            source="solvedac",
            status="running" if solvedac_running else ("completed" if problem_count > 0 else "pending"),
            last_synced_at=last_problem.created_at if last_problem else None,
            items_synced=problem_count
        ),
        SyncStatus(
            source="velog",
            status="running" if velog_running else ("completed" if post_count > 0 else "pending"),
            last_synced_at=last_post.created_at if last_post else None,
            items_synced=post_count
        ),
    ]


@router.get("/config", response_model=CollectorConfigResponse)
async def get_collector_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get collector configuration and connection status."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()

    # Check if data exists for each source
    has_github = db.query(Repo).filter(Repo.user_id == current_user.id).first() is not None
    has_solvedac = db.query(Problem).filter(Problem.user_id == current_user.id).first() is not None
    has_velog = db.query(BlogPost).filter(BlogPost.user_id == current_user.id).first() is not None
    
    # Get last sync times
    last_github = None
    last_solvedac = None
    last_velog = None
    
    if has_github:
        last_github = db.query(func.max(Repo.updated_at)).filter(Repo.user_id == current_user.id).scalar()
    if has_solvedac:
        last_solvedac = db.query(func.max(Problem.created_at)).filter(Problem.user_id == current_user.id).scalar()
    if has_velog:
        last_velog = db.query(func.max(BlogPost.created_at)).filter(BlogPost.user_id == current_user.id).scalar()
    
    return CollectorConfigResponse(
        github_username=current_user.github_username,
        github_connected=has_github,
        solvedac_username=profile.solvedac_handle if profile else None,
        solvedac_connected=has_solvedac,
        velog_username=profile.velog_id if profile else None,
        velog_connected=has_velog,
        last_github_sync=last_github,
        last_solvedac_sync=last_solvedac,
        last_velog_sync=last_velog
    )
