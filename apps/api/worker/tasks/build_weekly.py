import sys
sys.path.insert(0, '/app/packages/merge_timeline')
sys.path.insert(0, '/app/packages/merge_core')

from datetime import datetime, timedelta, date
from worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.models.weekly_summary import WeeklySummary
from app.models.commit import Commit
from app.models.problem import Problem
from app.models.note import Note
from sqlalchemy import func


@celery_app.task
def build_weekly_summary(user_id: str, week_start_date: str):
    """Build weekly summary for a single user and week."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        week_start = datetime.fromisoformat(week_start_date).date()
        week_end = week_start + timedelta(days=6)
        
        # Query data for the week
        commits = db.query(Commit).filter(
            Commit.user_id == user.id,
            Commit.committed_at >= week_start,
            Commit.committed_at <= week_end
        ).all()
        
        problems = db.query(Problem).filter(
            Problem.user_id == user.id,
            Problem.solved_at >= week_start,
            Problem.solved_at <= week_end
        ).all()
        
        notes = db.query(Note).filter(
            Note.user_id == user.id,
            Note.created_at >= week_start,
            Note.created_at <= week_end
        ).all()
        
        # Build aggregation
        from merge_timeline.aggregator import aggregate_week_data
        
        summary_json = aggregate_week_data(commits, problems, notes)
        
        # Upsert weekly summary
        existing = db.query(WeeklySummary).filter(
            WeeklySummary.user_id == user.id,
            WeeklySummary.week_start == week_start,
            WeeklySummary.week_end == week_end
        ).first()
        
        if existing:
            existing.commit_count = len(commits)
            existing.problem_count = len(problems)
            existing.note_count = len(notes)
            existing.summary_json = summary_json
        else:
            new_summary = WeeklySummary(
                user_id=user.id,
                week_start=week_start,
                week_end=week_end,
                commit_count=len(commits),
                problem_count=len(problems),
                note_count=len(notes),
                summary_json=summary_json,
            )
            db.add(new_summary)
        
        db.commit()
        return {"status": "success", "user_id": user_id, "week_start": week_start_date}
    finally:
        db.close()


@celery_app.task
def build_all_weekly_summaries():
    """Build weekly summaries for all users for the previous week."""
    db = SessionLocal()
    try:
        # Get last Monday
        today = date.today()
        days_since_monday = (today.weekday() - 0) % 7
        last_monday = today - timedelta(days=days_since_monday + 7)
        
        users = db.query(User).all()
        for user in users:
            build_weekly_summary.delay(str(user.id), last_monday.isoformat())
        
        return {"status": "queued", "user_count": len(users), "week_start": last_monday.isoformat()}
    finally:
        db.close()
