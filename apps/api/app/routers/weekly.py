from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.weekly_summary import WeeklySummary
from app.schemas.weekly import (
    WeeklyFilterRequest,
    WeeklySummaryCreate,
    WeeklySummaryListResponse,
    WeeklySummaryResponse,
    WeeklySummaryStats,
)

router = APIRouter()


def _serialize_weekly(summary: WeeklySummary) -> WeeklySummaryResponse:
    return WeeklySummaryResponse(
        id=str(summary.id),
        user_id=str(summary.user_id),
        week_start=summary.week_start,
        week_end=summary.week_end,
        commit_count=summary.commit_count or 0,
        problem_count=summary.problem_count or 0,
        note_count=summary.note_count or 0,
        summary_json=summary.summary_json or {},
        llm_summary=summary.llm_summary,
        status="completed" if summary.llm_summary else "pending",
        week=summary.week_start.isoformat(),
        created_at=summary.created_at,
        updated_at=summary.updated_at,
    )


@router.post("/generate")
async def generate_weekly_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate weekly report for current week."""
    today = datetime.utcnow().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    existing = (
        db.query(WeeklySummary)
        .filter(
            WeeklySummary.user_id == current_user.id,
            WeeklySummary.week_start == week_start,
            WeeklySummary.week_end == week_end,
        )
        .first()
    )

    if existing:
        from worker.tasks.forge_llm import generate_weekly_report_llm

        task = generate_weekly_report_llm.delay(str(current_user.id), str(existing.id))
        return {
            "message": "Weekly report generation started",
            "task_id": task.id,
            "weekly_id": str(existing.id),
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "status": "processing",
        }

    from worker.tasks.build_weekly import build_weekly_summary

    task = build_weekly_summary.delay(str(current_user.id), week_start.isoformat(), True)
    return {
        "message": "Weekly summary build and report generation queued",
        "task_id": task.id,
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "status": "processing",
    }


@router.post("/", response_model=WeeklySummaryResponse)
async def create_weekly_summary(
    request: WeeklySummaryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a weekly summary or regenerate existing one."""
    existing = (
        db.query(WeeklySummary)
        .filter(
            WeeklySummary.user_id == current_user.id,
            WeeklySummary.week_start == request.week_start,
            WeeklySummary.week_end == request.week_end,
        )
        .first()
    )

    if existing and not request.regenerate:
        raise HTTPException(
            status_code=400,
            detail="Weekly summary already exists. Set regenerate=true to regenerate.",
        )

    from worker.tasks.build_weekly import build_weekly_summary

    if existing and request.regenerate:
        existing.llm_summary = None
        existing.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)

        build_weekly_summary.delay(str(current_user.id), existing.week_start.isoformat(), True)
        return _serialize_weekly(existing)

    summary = WeeklySummary(
        user_id=current_user.id,
        week_start=request.week_start,
        week_end=request.week_end,
        commit_count=0,
        problem_count=0,
        note_count=0,
        summary_json={},
        llm_summary=None,
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)

    build_weekly_summary.delay(str(current_user.id), request.week_start.isoformat(), False)
    return _serialize_weekly(summary)


@router.get("/stats/overview", response_model=WeeklySummaryStats)
async def get_weekly_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get weekly summary statistics."""
    summaries = db.query(WeeklySummary).filter(WeeklySummary.user_id == current_user.id).all()

    if not summaries:
        return WeeklySummaryStats(
            total_summaries=0,
            total_commits=0,
            total_problems=0,
            total_blogs=0,
            average_commits_per_week=0.0,
            most_productive_week=None,
        )

    total_commits = sum(summary.commit_count or 0 for summary in summaries)
    total_problems = sum(summary.problem_count or 0 for summary in summaries)
    total_blogs = sum(summary.note_count or 0 for summary in summaries)
    average_commits = total_commits / len(summaries)

    most_productive = max(
        summaries,
        key=lambda summary: (summary.commit_count or 0)
        + (summary.problem_count or 0)
        + (summary.note_count or 0),
    )

    return WeeklySummaryStats(
        total_summaries=len(summaries),
        total_commits=total_commits,
        total_problems=total_problems,
        total_blogs=total_blogs,
        average_commits_per_week=round(average_commits, 2),
        most_productive_week=most_productive.week_start.isoformat() if most_productive else None,
    )


@router.get("", response_model=WeeklySummaryListResponse)
@router.get("/", response_model=WeeklySummaryListResponse)
async def list_weekly_summaries(
    filter_request: WeeklyFilterRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List weekly summaries for current user."""
    query = db.query(WeeklySummary).filter(WeeklySummary.user_id == current_user.id)

    if filter_request.year:
        query = query.filter(
            func.extract("year", WeeklySummary.week_start) == filter_request.year
        )
    if filter_request.month:
        query = query.filter(
            func.extract("month", WeeklySummary.week_start) == filter_request.month
        )

    total = query.count()
    summaries = (
        query.order_by(WeeklySummary.week_start.desc())
        .offset((filter_request.page - 1) * filter_request.page_size)
        .limit(filter_request.page_size)
        .all()
    )

    return WeeklySummaryListResponse(
        summaries=[_serialize_weekly(summary) for summary in summaries],
        total=total,
        page=filter_request.page,
        page_size=filter_request.page_size,
    )


@router.get("/{weekly_id}", response_model=WeeklySummaryResponse)
async def get_weekly_summary(
    weekly_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific weekly summary by ID."""
    summary = (
        db.query(WeeklySummary)
        .filter(
            WeeklySummary.id == weekly_id,
            WeeklySummary.user_id == current_user.id,
        )
        .first()
    )

    if not summary:
        raise HTTPException(status_code=404, detail="Weekly summary not found")

    return _serialize_weekly(summary)


@router.delete("/{weekly_id}")
async def delete_weekly_summary(
    weekly_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a weekly summary."""
    summary = (
        db.query(WeeklySummary)
        .filter(
            WeeklySummary.id == weekly_id,
            WeeklySummary.user_id == current_user.id,
        )
        .first()
    )

    if not summary:
        raise HTTPException(status_code=404, detail="Weekly summary not found")

    db.delete(summary)
    db.commit()
    return {"message": "Weekly summary deleted successfully"}
