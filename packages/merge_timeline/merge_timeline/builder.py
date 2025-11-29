"""Weekly summary builder."""
from datetime import date, timedelta
from sqlalchemy.orm import Session
from typing import Optional


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
    
    # TODO: Implement actual data fetching and aggregation
    # 1. Query commits, problems, notes for the week
    # 2. Call aggregator.aggregate_week_data()
    # 3. Create/update WeeklySummary in database
    
    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "commit_count": 0,
        "problem_count": 0,
        "note_count": 0,
        "summary_json": {},
    }
