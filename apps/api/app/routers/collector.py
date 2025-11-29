from fastapi import APIRouter, Depends, BackgroundTasks
from app.deps import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/trigger/github")
async def trigger_github_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger manual GitHub sync."""
    # TODO: Implement Celery task trigger
    # from worker.tasks.sync_github import sync_github_for_user
    # sync_github_for_user.delay(str(current_user.id))
    
    return {"message": "GitHub sync triggered", "status": "queued"}


@router.post("/trigger/solvedac")
async def trigger_solvedac_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger manual solved.ac sync."""
    # TODO: Implement Celery task trigger
    # from worker.tasks.sync_solvedac import sync_solvedac_for_user
    # sync_solvedac_for_user.delay(str(current_user.id))
    
    return {"message": "solved.ac sync triggered", "status": "queued"}


@router.post("/trigger/velog")
async def trigger_velog_sync(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Trigger manual Velog sync."""
    # TODO: Implement Celery task trigger
    # from worker.tasks.sync_velog import sync_velog_for_user
    # sync_velog_for_user.delay(str(current_user.id))
    
    return {"message": "Velog sync triggered", "status": "queued"}


@router.get("/status")
async def get_sync_status(current_user: User = Depends(get_current_user)):
    """Get sync status for all sources."""
    # TODO: Implement actual status checking
    return {
        "github": {"status": "idle", "last_synced": None},
        "solvedac": {"status": "idle", "last_synced": None},
        "velog": {"status": "idle", "last_synced": None},
    }
