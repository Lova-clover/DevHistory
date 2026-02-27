"""Analytics event ingestion and admin metrics."""
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.analytics_event import AnalyticsEvent
from app.models.user import User
from app.config import settings

router = APIRouter()


# ── Event Ingestion ──────────────────────────────────────────────

class EventCreate(BaseModel):
    event_name: str
    path: Optional[str] = None
    referrer: Optional[str] = None
    meta: Optional[dict] = None


def _hash_ip(ip: str) -> str:
    """One-way hash of IP with daily salt."""
    salt = datetime.utcnow().strftime("%Y-%m-%d")
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()[:16]


@router.post("/event", status_code=204)
async def track_event(
    data: EventCreate,
    request: Request,
    db: Session = Depends(get_db),
):
    """Record an analytics event (anonymous or authenticated)."""
    # Try to get user from cookie (don't fail if not authed)
    user_id = None
    try:
        from app.deps import get_current_user_optional
        user_id = None  # Will add optional dep later
    except ImportError:
        pass

    # Extract session id from cookie if present
    session_id = request.cookies.get("_dh_sid")

    ip = request.client.host if request.client else "unknown"

    event = AnalyticsEvent(
        event_name=data.event_name,
        user_id=user_id,
        session_id=session_id,
        path=data.path,
        referrer=data.referrer,
        user_agent=request.headers.get("user-agent", "")[:512],
        ip_hash=_hash_ip(ip),
        meta=data.meta,
    )
    db.add(event)
    db.commit()
    return None


# ── Admin Guard ──────────────────────────────────────────────────

def _require_admin(current_user: User = Depends(get_current_user)):
    """Dependency that ensures user is admin."""
    admin_usernames = [u.strip().lower() for u in settings.ADMIN_GITHUB_USERNAMES.split(",") if u.strip()]
    is_admin_by_list = current_user.github_username and current_user.github_username.lower() in admin_usernames
    if not current_user.is_admin and not is_admin_by_list:
        raise HTTPException(403, "Admin access required")
    return current_user


# ── Admin Metrics ────────────────────────────────────────────────

@router.get("/admin/overview")
async def admin_overview(
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """High-level metrics: total users, DAU, MAU, total events, etc."""
    now = datetime.utcnow()
    today = now.date()
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)

    total_users = db.query(func.count(User.id)).scalar() or 0

    # DAU: unique user_ids with events today
    dau = db.query(func.count(func.distinct(AnalyticsEvent.user_id))).filter(
        cast(AnalyticsEvent.created_at, Date) == today,
        AnalyticsEvent.user_id.isnot(None),
    ).scalar() or 0

    # MAU: unique user_ids last 30 days
    mau = db.query(func.count(func.distinct(AnalyticsEvent.user_id))).filter(
        AnalyticsEvent.created_at >= thirty_days_ago,
        AnalyticsEvent.user_id.isnot(None),
    ).scalar() or 0

    # Total events last 7 days
    events_7d = db.query(func.count(AnalyticsEvent.id)).filter(
        AnalyticsEvent.created_at >= seven_days_ago,
    ).scalar() or 0

    # Unique sessions today (PV proxy)
    pv_today = db.query(func.count(AnalyticsEvent.id)).filter(
        cast(AnalyticsEvent.created_at, Date) == today,
        AnalyticsEvent.event_name == "page_view",
    ).scalar() or 0

    uv_today = db.query(func.count(func.distinct(AnalyticsEvent.ip_hash))).filter(
        cast(AnalyticsEvent.created_at, Date) == today,
        AnalyticsEvent.event_name == "page_view",
    ).scalar() or 0

    return {
        "total_users": total_users,
        "dau": dau,
        "mau": mau,
        "events_7d": events_7d,
        "pv_today": pv_today,
        "uv_today": uv_today,
    }


@router.get("/admin/timeseries")
async def admin_timeseries(
    days: int = 30,
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Daily PV/UV for the last N days."""
    if days > 90:
        days = 90
    start = datetime.utcnow() - timedelta(days=days)

    rows = (
        db.query(
            cast(AnalyticsEvent.created_at, Date).label("day"),
            func.count(AnalyticsEvent.id).label("pv"),
            func.count(func.distinct(AnalyticsEvent.ip_hash)).label("uv"),
        )
        .filter(
            AnalyticsEvent.created_at >= start,
            AnalyticsEvent.event_name == "page_view",
        )
        .group_by(cast(AnalyticsEvent.created_at, Date))
        .order_by(cast(AnalyticsEvent.created_at, Date))
        .all()
    )

    return [
        {"date": str(row.day), "pv": row.pv, "uv": row.uv}
        for row in rows
    ]


@router.get("/admin/top-pages")
async def admin_top_pages(
    days: int = 7,
    current_user: User = Depends(_require_admin),
    db: Session = Depends(get_db),
):
    """Top visited pages in the last N days."""
    start = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            AnalyticsEvent.path,
            func.count(AnalyticsEvent.id).label("views"),
        )
        .filter(
            AnalyticsEvent.created_at >= start,
            AnalyticsEvent.event_name == "page_view",
            AnalyticsEvent.path.isnot(None),
        )
        .group_by(AnalyticsEvent.path)
        .order_by(func.count(AnalyticsEvent.id).desc())
        .limit(20)
        .all()
    )
    return [{"path": row.path, "views": row.views} for row in rows]
