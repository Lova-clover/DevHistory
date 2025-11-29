"""Chart data API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.repo import Repo
from app.models.commit import Commit
from app.models.problem import Problem
from typing import List, Dict

router = APIRouter()


@router.get("/commit-activity")
async def get_commit_activity(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get commit activity for the last N days."""
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # Query commits grouped by date
    commits_by_date = db.query(
        func.date(Commit.committed_at).label("date"),
        func.count(Commit.id).label("count")
    ).join(Repo).filter(
        Repo.user_id == current_user.id,
        Commit.committed_at >= start_date
    ).group_by(func.date(Commit.committed_at)).all()
    
    # Create a complete date range
    data = []
    for i in range(days):
        date = (start_date + timedelta(days=i)).date()
        count = next((c.count for c in commits_by_date if c.date == date), 0)
        data.append({
            "date": date.strftime("%m/%d"),
            "commits": count
        })
    
    return {"data": data}


@router.get("/language-distribution")
async def get_language_distribution(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get programming language distribution from repos."""
    # Query repos grouped by language
    language_stats = db.query(
        Repo.language,
        func.count(Repo.id).label("count")
    ).filter(
        Repo.user_id == current_user.id,
        Repo.language.isnot(None)
    ).group_by(Repo.language).order_by(func.count(Repo.id).desc()).all()
    
    # Calculate total and percentages
    total = sum(stat.count for stat in language_stats)
    
    data = [
        {
            "name": stat.language,
            "value": stat.count,
            "percentage": round((stat.count / total * 100), 1) if total > 0 else 0
        }
        for stat in language_stats
    ]
    
    return {"data": data}


@router.get("/activity-heatmap")
async def get_activity_heatmap(
    days: int = 365,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activity heatmap data for the last N days."""
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)
    
    # Query all activity grouped by date
    commits_by_date = db.query(
        func.date(Commit.committed_at).label("date"),
        func.count(Commit.id).label("count")
    ).join(Repo).filter(
        Repo.user_id == current_user.id,
        Commit.committed_at >= start_date
    ).group_by(func.date(Commit.committed_at)).all()
    
    problems_by_date = db.query(
        func.date(Problem.solved_at).label("date"),
        func.count(Problem.id).label("count")
    ).filter(
        Problem.user_id == current_user.id,
        Problem.solved_at >= start_date
    ).group_by(func.date(Problem.solved_at)).all()
    
    # Combine activities by date
    activity_map = {}
    for commit in commits_by_date:
        activity_map[commit.date] = activity_map.get(commit.date, 0) + commit.count
    
    for problem in problems_by_date:
        activity_map[problem.date] = activity_map.get(problem.date, 0) + problem.count
    
    # Create heatmap data (365 days)
    data = []
    for i in range(days):
        date = (start_date + timedelta(days=i)).date()
        count = activity_map.get(date, 0)
        data.append({
            "date": date.isoformat(),
            "count": count
        })
    
    return {"data": data}


@router.get("/weekly-comparison")
async def get_weekly_comparison(
    weeks: int = 8,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly activity comparison for the last N weeks."""
    now = datetime.utcnow()
    data = []
    
    for i in range(weeks):
        week_end = now - timedelta(days=i*7)
        week_start = week_end - timedelta(days=7)
        
        commits = db.query(func.count(Commit.id)).join(Repo).filter(
            Repo.user_id == current_user.id,
            Commit.committed_at >= week_start,
            Commit.committed_at < week_end
        ).scalar() or 0
        
        problems = db.query(func.count(Problem.id)).filter(
            Problem.user_id == current_user.id,
            Problem.solved_at >= week_start,
            Problem.solved_at < week_end
        ).scalar() or 0
        
        data.insert(0, {
            "week": week_start.strftime("%m/%d"),
            "commits": commits,
            "problems": problems,
            "total": commits + problems
        })
    
    return {"data": data}
