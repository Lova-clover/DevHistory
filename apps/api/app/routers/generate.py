from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.weekly_summary import WeeklySummary
from app.models.repo import Repo
from app.models.generated_content import GeneratedContent

router = APIRouter()


@router.post("/weekly-report/{weekly_id}")
async def generate_weekly_report(
    weekly_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate LLM-based weekly report."""
    summary = db.query(WeeklySummary).filter(
        WeeklySummary.id == weekly_id,
        WeeklySummary.user_id == current_user.id
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Weekly summary not found")
    
    # Trigger LLM generation task
    from worker.tasks.forge_llm import generate_weekly_report_llm
    task = generate_weekly_report_llm.delay(str(current_user.id), str(weekly_id))
    
    return {
        "message": "Weekly report generation started",
        "task_id": task.id,
        "status": "processing"
    }


@router.post("/repo-blog/{repo_id}")
async def generate_repo_blog(
    repo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate blog post draft for a repository."""
    repo = db.query(Repo).filter(
        Repo.id == repo_id,
        Repo.user_id == current_user.id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # Trigger LLM generation task
    from worker.tasks.forge_llm import generate_repo_blog_llm
    task = generate_repo_blog_llm.delay(str(current_user.id), str(repo_id))
    
    return {
        "message": "Repo blog generation started",
        "task_id": task.id,
        "status": "processing"
    }
