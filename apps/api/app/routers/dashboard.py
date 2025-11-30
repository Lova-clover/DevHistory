from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.repo import Repo
from app.models.commit import Commit
from app.models.problem import Problem
from app.models.blog_post import BlogPost
from app.models.note import Note
from app.schemas.profile import DashboardStats, ActivityTimeline, ActivityTimelineResponse

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for the current user."""
    # Calculate time ranges
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # Get total counts
    total_repos = db.query(func.count(Repo.id)).filter(Repo.user_id == current_user.id).scalar() or 0
    total_commits = db.query(func.count(Commit.id)).join(Repo).filter(Repo.user_id == current_user.id).scalar() or 0
    total_problems = db.query(func.count(Problem.id)).filter(Problem.user_id == current_user.id).scalar() or 0
    total_blogs = db.query(func.count(BlogPost.id)).filter(BlogPost.user_id == current_user.id).scalar() or 0
    
    # Get recent activity counts
    commits_this_week = db.query(func.count(Commit.id)).join(Repo).filter(
        Repo.user_id == current_user.id,
        Commit.committed_at >= week_ago
    ).scalar() or 0
    
    commits_this_month = db.query(func.count(Commit.id)).join(Repo).filter(
        Repo.user_id == current_user.id,
        Commit.committed_at >= month_ago
    ).scalar() or 0
    
    problems_this_week = db.query(func.count(Problem.id)).filter(
        Problem.user_id == current_user.id,
        Problem.solved_at >= week_ago
    ).scalar() or 0
    
    problems_this_month = db.query(func.count(Problem.id)).filter(
        Problem.user_id == current_user.id,
        Problem.solved_at >= month_ago
    ).scalar() or 0
    
    # Calculate streaks
    current_streak = calculate_streak(current_user.id, db)
    longest_streak = calculate_longest_streak(current_user.id, db)
    
    return DashboardStats(
        total_repos=total_repos,
        total_commits=total_commits,
        total_problems_solved=total_problems,
        total_blog_posts=total_blogs,
        commits_this_week=commits_this_week,
        commits_this_month=commits_this_month,
        problems_this_week=problems_this_week,
        problems_this_month=problems_this_month,
        current_streak=current_streak,
        longest_streak=longest_streak
    )


@router.get("/summary")
async def get_dashboard_summary(
    range: str = Query("week", pattern="^(week|month|year)$"),
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
    
    # Count commits in current period
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
    
    # Count total repos (all time)
    repo_count = db.query(func.count(Repo.id)).filter(
        Repo.user_id == current_user.id
    ).scalar()
    
    # Count weekly reports (all time)
    from app.models.weekly_summary import WeeklySummary
    weekly_report_count = db.query(func.count(WeeklySummary.id)).filter(
        WeeklySummary.user_id == current_user.id
    ).scalar()
    
    # Count total blog posts (all time)
    blog_count = db.query(func.count(BlogPost.id)).filter(
        BlogPost.user_id == current_user.id
    ).scalar()
    
    # Count total commits (all time) for display
    total_commits = db.query(func.count(Commit.id)).filter(
        Commit.user_id == current_user.id
    ).scalar()
    
    # Calculate streaks
    current_streak = calculate_streak(current_user.id, db)
    longest_streak = calculate_longest_streak(current_user.id, db)
    
    # Calculate previous period data for trends
    if range == "week":
        prev_start = start_date - timedelta(days=7)
        prev_end = start_date
    elif range == "month":
        prev_start = start_date - timedelta(days=30)
        prev_end = start_date
    else:  # year
        prev_start = start_date - timedelta(days=365)
        prev_end = start_date
    
    prev_commit_count = db.query(func.count(Commit.id)).filter(
        Commit.user_id == current_user.id,
        Commit.committed_at >= prev_start,
        Commit.committed_at < prev_end
    ).scalar() or 0
    
    # Count repos created in previous period
    prev_repo_count = db.query(func.count(Repo.id)).filter(
        Repo.user_id == current_user.id,
        Repo.created_at >= prev_start,
        Repo.created_at < prev_end
    ).scalar() or 0
    
    # Count repos created in current period
    current_period_repos = db.query(func.count(Repo.id)).filter(
        Repo.user_id == current_user.id,
        Repo.created_at >= start_date
    ).scalar() or 0
    
    # Weekly reports in this week
    one_week_ago = now - timedelta(days=7)
    recent_weekly_count = db.query(func.count(WeeklySummary.id)).filter(
        WeeklySummary.user_id == current_user.id,
        WeeklySummary.created_at >= one_week_ago
    ).scalar() or 0
    
    # Count blogs in previous period
    prev_blog_count = db.query(func.count(BlogPost.id)).filter(
        BlogPost.user_id == current_user.id,
        BlogPost.published_at >= prev_start,
        BlogPost.published_at < prev_end
    ).scalar() or 0
    
    # Count blogs in current period
    current_period_blogs = db.query(func.count(BlogPost.id)).filter(
        BlogPost.user_id == current_user.id,
        BlogPost.published_at >= start_date
    ).scalar() or 0
    
    # Calculate trends (show difference, not percentage)
    commit_diff = commit_count - prev_commit_count
    
    repo_diff = current_period_repos - prev_repo_count
    blog_diff = current_period_blogs - prev_blog_count
    
    return {
        "range": range,
        "commit_count": commit_count or 0,
        "total_commits": total_commits or 0,
        "problem_count": problem_count or 0,
        "note_count": note_count or 0,
        "repo_count": repo_count or 0,
        "weekly_report_count": weekly_report_count or 0,
        "blog_count": blog_count or 0,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "start_date": start_date.isoformat(),
        "end_date": now.isoformat(),
        "commit_diff": commit_diff,
        "repo_diff": repo_diff,
        "recent_weekly_count": recent_weekly_count,
        "blog_diff": blog_diff,
    }


def calculate_streak(user_id: int, db: Session) -> int:
    """Calculate current consecutive days of activity."""
    # Get all activity dates
    commit_dates = db.query(func.date(Commit.committed_at)).join(Repo).filter(
        Repo.user_id == user_id
    ).distinct().all()
    
    problem_dates = db.query(func.date(Problem.solved_at)).filter(
        Problem.user_id == user_id
    ).distinct().all()
    
    blog_dates = db.query(func.date(BlogPost.published_at)).filter(
        BlogPost.user_id == user_id
    ).distinct().all()
    
    # Combine and sort dates
    all_dates = set()
    for (date,) in commit_dates + problem_dates + blog_dates:
        if date:
            all_dates.add(date)
    
    if not all_dates:
        return 0
    
    sorted_dates = sorted(all_dates, reverse=True)
    today = datetime.utcnow().date()
    
    # Check if there's activity today or yesterday
    if sorted_dates[0] < today - timedelta(days=1):
        return 0
    
    streak = 0
    expected_date = today
    
    for date in sorted_dates:
        if date == expected_date or date == expected_date - timedelta(days=1):
            streak += 1
            expected_date = date - timedelta(days=1)
        else:
            break
    
    return streak


def calculate_longest_streak(user_id: int, db: Session) -> int:
    """Calculate longest consecutive days of activity in history."""
    # Get all activity dates
    commit_dates = db.query(func.date(Commit.committed_at)).join(Repo).filter(
        Repo.user_id == user_id
    ).distinct().all()
    
    problem_dates = db.query(func.date(Problem.solved_at)).filter(
        Problem.user_id == user_id
    ).distinct().all()
    
    blog_dates = db.query(func.date(BlogPost.published_at)).filter(
        BlogPost.user_id == user_id
    ).distinct().all()
    
    # Combine and sort dates
    all_dates = set()
    for (date,) in commit_dates + problem_dates + blog_dates:
        if date:
            all_dates.add(date)
    
    if not all_dates:
        return 0
    
    sorted_dates = sorted(all_dates)
    
    longest = 1
    current = 1
    
    for i in range(1, len(sorted_dates)):
        if sorted_dates[i] == sorted_dates[i-1] + timedelta(days=1):
            current += 1
            longest = max(longest, current)
        else:
            current = 1
    
    return longest


@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent activity for the current user - commits only."""
    activities = []
    
    # Get recent commits (use committed_at for sorting)
    recent_commits = db.query(Commit).filter(
        Commit.user_id == current_user.id
    ).order_by(Commit.committed_at.desc()).limit(limit).all()
    
    for commit in recent_commits:
        repo = db.query(Repo).filter(Repo.id == commit.repo_id).first()
        if commit.committed_at:  # Only add if committed_at exists
            activities.append({
                "type": "commit",
                "title": f"{repo.full_name if repo else 'Unknown'}: {commit.message[:50]}{'...' if len(commit.message) > 50 else ''}",
                "timestamp": commit.committed_at.isoformat(),
                "color": "blue"
            })
    
    # Sort by timestamp (already sorted but just to be sure)
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:limit]
