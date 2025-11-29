"""Weekly summary builder."""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from typing import Optional
from app.models.commit import Commit
from app.models.problem import Problem
from app.models.note import Note
from app.models.weekly_summary import WeeklySummary
from merge_timeline.aggregator import aggregate_week_data


def build_weekly_summary(user_id: str, week_start: date, db: Session) -> Optional[dict]:
    """
    Build weekly summary for a user.
    
    Args:
        user_id: User UUID
        week_start: Start date of the week (Monday)
        db: Database session
        
    Returns:
        Weekly summary data or None if failed
    """
    week_end = week_start + timedelta(days=6)
    
    # Query commits, problems, notes for the week
    commits = db.query(Commit).filter(
        Commit.user_id == user_id,
        Commit.committed_at >= week_start,
        Commit.committed_at <= week_end
    ).all()
    
    problems = db.query(Problem).filter(
        Problem.user_id == user_id,
        Problem.solved_at >= week_start,
        Problem.solved_at <= week_end
    ).all()
    
    notes = db.query(Note).filter(
        Note.user_id == user_id,
        Note.created_at >= week_start,
        Note.created_at <= week_end
    ).all()
    
    # Aggregate data
    summary_json = aggregate_week_data(commits, problems, notes)
    
    # Create/update WeeklySummary in database
    existing = db.query(WeeklySummary).filter(
        WeeklySummary.user_id == user_id,
        WeeklySummary.week_start == week_start,
        WeeklySummary.week_end == week_end
    ).first()
    
    if existing:
        existing.commit_count = len(commits)
        existing.problem_count = len(problems)
        existing.note_count = len(notes)
        existing.summary_json = summary_json
        weekly = existing
    else:
        weekly = WeeklySummary(
            user_id=user_id,
            week_start=week_start,
            week_end=week_end,
            commit_count=len(commits),
            problem_count=len(problems),
            note_count=len(notes),
            summary_json=summary_json
        )
        db.add(weekly)
    
    db.commit()
    
    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "commit_count": len(commits),
        "problem_count": len(problems),
        "note_count": len(notes),
        "summary_json": summary_json,
    }
