from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.commit import Commit
from app.models.problem import Problem
from app.models.note import Note

router = APIRouter()


@router.get("/summary")
async def get_dashboard_summary(
    range: str = Query("week", regex="^(week|month|year)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard summary for specified time range."""
    now = datetime.utcnow()
    
    if range == "week":
        start_date = now - timedelta(days=7)
    elif range == "month":
        start_date = now - timedelta(days=30)
    else:  # year
        start_date = now - timedelta(days=365)
    
    # Count commits
    commit_count = db.query(func.count(Commit.id)).filter(
        Commit.user_id == current_user.id,
        Commit.committed_at >= start_date
    ).scalar()
    
    # Count problems
    problem_count = db.query(func.count(Problem.id)).filter(
        Problem.user_id == current_user.id,
        Problem.solved_at >= start_date
    ).scalar()
    
    # Count notes
    note_count = db.query(func.count(Note.id)).filter(
        Note.user_id == current_user.id,
        Note.created_at >= start_date
    ).scalar()
    
    return {
        "range": range,
        "commit_count": commit_count or 0,
        "problem_count": problem_count or 0,
        "note_count": note_count or 0,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
    }
