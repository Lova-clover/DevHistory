from worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.models.oauth_account import OAuthAccount
import httpx


@celery_app.task
def sync_github_for_user(user_id: str):
    """Sync GitHub repos and commits for a single user."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Get GitHub OAuth account
        github_account = db.query(OAuthAccount).filter(
            OAuthAccount.user_id == user.id,
            OAuthAccount.provider == "github"
        ).first()
        
        if not github_account:
            return {"error": "GitHub account not connected"}
        
        # TODO: Implement actual GitHub API calls
        # from merge_collector.github import sync_repos, sync_commits
        # sync_repos(user, github_account.access_token, db)
        # sync_commits(user, github_account.access_token, db)
        
        return {"status": "success", "user_id": user_id}
    finally:
        db.close()


@celery_app.task
def sync_all_users_github():
    """Sync GitHub for all active users."""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            sync_github_for_user.delay(str(user.id))
        return {"status": "queued", "user_count": len(users)}
    finally:
        db.close()
