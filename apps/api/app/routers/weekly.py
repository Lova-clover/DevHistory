from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.weekly_summary import WeeklySummary
from pydantic import BaseModel

router = APIRouter()


class WeeklySummaryResponse(BaseModel):
    id: str
    week_start: str
    week_end: str
    commit_count: int
    problem_count: int
    note_count: int
    summary_json: dict
    llm_summary: str | None
    
    class Config:
        from_attributes = True


@router.get("/")
async def list_weekly_summaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all weekly summaries for current user."""
    summaries = db.query(WeeklySummary).filter(
        WeeklySummary.user_id == current_user.id
    ).order_by(WeeklySummary.week_start.desc()).all()
    
    return [
        {
            "id": str(summary.id),
            "week_start": summary.week_start.isoformat(),
            "week_end": summary.week_end.isoformat(),
            "commit_count": summary.commit_count,
            "problem_count": summary.problem_count,
            "note_count": summary.note_count,
            "has_llm_summary": summary.llm_summary is not None,
        }
        for summary in summaries
    ]


@router.get("/{weekly_id}")
async def get_weekly_summary(
    weekly_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed weekly summary."""
    summary = db.query(WeeklySummary).filter(
        WeeklySummary.id == weekly_id,
        WeeklySummary.user_id == current_user.id
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Weekly summary not found")
    
    return {
        "id": str(summary.id),
        "week_start": summary.week_start.isoformat(),
        "week_end": summary.week_end.isoformat(),
        "commit_count": summary.commit_count,
        "problem_count": summary.problem_count,
        "note_count": summary.note_count,
        "summary_json": summary.summary_json,
        "llm_summary": summary.llm_summary,
    }
