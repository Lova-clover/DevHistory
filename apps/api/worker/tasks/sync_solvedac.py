from worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.models.user_profile import UserProfile


@celery_app.task
def sync_solvedac_for_user(user_id: str):
    """Sync solved.ac problems for a single user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Get solved.ac handle
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile or not profile.solvedac_handle:
            return {"error": "solved.ac handle not configured"}
        
        # TODO: Implement actual solved.ac API calls
        # from merge_collector.solvedac import sync_problems
        # sync_problems(user, profile.solvedac_handle, db)
        
        return {"status": "success", "user_id": user_id}
    finally:
        db.close()


@celery_app.task
def sync_all_users_solvedac():
    """Sync solved.ac for all active users."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            sync_solvedac_for_user.delay(str(user.id))
        return {"status": "queued", "user_count": len(users)}
    finally:
        db.close()
