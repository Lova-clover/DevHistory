from worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User


@celery_app.task
def generate_weekly_report_llm(user_id: str, weekly_summary_id: str):
    """Generate LLM-based weekly report."""
    db = SessionLocal()
    try:
        # TODO: Implement actual LLM generation
        # from merge_forge import generate_weekly_report
        # content = generate_weekly_report(user_id, weekly_summary_id, db)
        
        return {"status": "success", "user_id": user_id, "weekly_id": weekly_summary_id}
    finally:
        db.close()


@celery_app.task
def generate_repo_blog_llm(user_id: str, repo_id: str):
    """Generate LLM-based repo blog post."""
    db = SessionLocal()
    try:
        # TODO: Implement actual LLM generation
        # from merge_forge import generate_repo_blog
        # content = generate_repo_blog(user_id, repo_id, db)
        
        return {"status": "success", "user_id": user_id, "repo_id": repo_id}
    finally:
        db.close()
