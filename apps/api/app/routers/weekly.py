from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.weekly_summary import WeeklySummary
from app.schemas.weekly import (
    WeeklySummaryCreate,
    WeeklySummaryResponse,
    WeeklySummaryListResponse,
    WeeklySummaryStats,
    WeeklyFilterRequest
)
from sqlalchemy import func
from datetime import datetime

router = APIRouter()


@router.post("/", response_model=WeeklySummaryResponse)
async def create_weekly_summary(
    request: WeeklySummaryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new weekly summary or regenerate existing one."""
    # Check if summary already exists
    existing = db.query(WeeklySummary).filter(
        WeeklySummary.user_id == current_user.id,
        WeeklySummary.start_date == request.start_date,
        WeeklySummary.end_date == request.end_date
    ).first()
    
    if existing and not request.regenerate:
        raise HTTPException(
            status_code=400, 
            detail="Weekly summary already exists. Set regenerate=true to regenerate."
        )
    
    if existing and request.regenerate:
        # Reset existing summary
        existing.status = "pending"
        existing.summary_text = ""
        existing.highlights = []
        existing.updated_at = datetime.utcnow()
        db.commit()
        
        # Trigger regeneration
        from worker.tasks.build_weekly import build_weekly_summary
        task = build_weekly_summary.delay(str(current_user.id), str(existing.id))
        
        return WeeklySummaryResponse.model_validate(existing)
    
    # Create new summary
    summary = WeeklySummary(
        user_id=current_user.id,
        start_date=request.start_date,
        end_date=request.end_date,
        summary_text="",
        highlights=[],
        commit_count=0,
        problem_count=0,
        blog_count=0,
        status="pending"
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    
    # Trigger background task to build summary
    from worker.tasks.build_weekly import build_weekly_summary
    task = build_weekly_summary.delay(str(current_user.id), str(summary.id))
    
    return WeeklySummaryResponse.model_validate(summary)


@router.get("/", response_model=WeeklySummaryListResponse)
async def list_weekly_summaries(
    filter_request: WeeklyFilterRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all weekly summaries for current user with optional filters."""
    query = db.query(WeeklySummary).filter(WeeklySummary.user_id == current_user.id)
    
    if filter_request.year:
        query = query.filter(func.extract('year', WeeklySummary.start_date) == filter_request.year)
    if filter_request.month:
        query = query.filter(func.extract('month', WeeklySummary.start_date) == filter_request.month)
    
    total = query.count()
    summaries = query.order_by(WeeklySummary.start_date.desc()).offset(
        (filter_request.page - 1) * filter_request.page_size
    ).limit(filter_request.page_size).all()
    
    return WeeklySummaryListResponse(
        summaries=[WeeklySummaryResponse.model_validate(s) for s in summaries],
        total=total,
        page=filter_request.page,
        page_size=filter_request.page_size
    )


@router.get("/{weekly_id}", response_model=WeeklySummaryResponse)
async def get_weekly_summary(
    weekly_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific weekly summary by ID."""
    summary = db.query(WeeklySummary).filter(
        WeeklySummary.id == weekly_id,
        WeeklySummary.user_id == current_user.id
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Weekly summary not found")
    
    return WeeklySummaryResponse.model_validate(summary)


@router.get("/stats/overview", response_model=WeeklySummaryStats)
async def get_weekly_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly summary statistics."""
    summaries = db.query(WeeklySummary).filter(
        WeeklySummary.user_id == current_user.id,
        WeeklySummary.status == "completed"
    ).all()
    
    if not summaries:
        return WeeklySummaryStats(
            total_summaries=0,
            total_commits=0,
            total_problems=0,
            total_blogs=0,
            average_commits_per_week=0.0,
            most_productive_week=None
        )
    
    total_commits = sum(s.commit_count for s in summaries)
    total_problems = sum(s.problem_count for s in summaries)
    total_blogs = sum(s.blog_count for s in summaries)
    
    average_commits = total_commits / len(summaries) if summaries else 0
    
    # Find most productive week
    most_productive = max(summaries, key=lambda s: s.commit_count + s.problem_count + s.blog_count)
    most_productive_week = most_productive.start_date.isoformat() if most_productive else None
    
    return WeeklySummaryStats(
        total_summaries=len(summaries),
        total_commits=total_commits,
        total_problems=total_problems,
        total_blogs=total_blogs,
        average_commits_per_week=round(average_commits, 2),
        most_productive_week=most_productive_week
    )


@router.delete("/{weekly_id}")
async def delete_weekly_summary(
    weekly_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a weekly summary."""
    summary = db.query(WeeklySummary).filter(
        WeeklySummary.id == weekly_id,
        WeeklySummary.user_id == current_user.id
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Weekly summary not found")
    
    db.delete(summary)
    db.commit()
    
    return {"message": "Weekly summary deleted successfully"}

