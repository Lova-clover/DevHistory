from worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.models.user_profile import UserProfile


@celery_app.task
def sync_velog_for_user(user_id: str):
    """Sync Velog posts for a single user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Get Velog ID
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        if not profile or not profile.velog_id:
            return {"error": "Velog ID not configured"}
        
        # Sync blog posts
        import asyncio
        from merge_collector.velog import sync_blog_posts
        
        posts = asyncio.run(sync_blog_posts(str(user.id), profile.velog_id, db))
        
        return {"status": "success", "user_id": user_id, "posts_synced": len(posts)}
    finally:
        db.close()


@celery_app.task
def sync_all_users_velog():
    """Sync Velog for all active users."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            sync_velog_for_user.delay(str(user.id))
        return {"status": "queued", "user_count": len(users)}
    finally:
        db.close()
