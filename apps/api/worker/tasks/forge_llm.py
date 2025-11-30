import sys
sys.path.insert(0, '/app/packages/merge_forge')
sys.path.insert(0, '/app/packages/merge_styler')
sys.path.insert(0, '/app/packages/merge_core')

from worker.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.models.weekly_summary import WeeklySummary
from app.models.repo import Repo
from app.models.style_profile import StyleProfile
from app.models.generated_content import GeneratedContent


@celery_app.task
def generate_weekly_report_llm(user_id: str, weekly_summary_id: str):
    """Generate LLM-based weekly report."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        weekly_summary = db.query(WeeklySummary).filter(WeeklySummary.id == weekly_summary_id).first()
        if not weekly_summary:
            return {"error": "Weekly summary not found"}
        
        style_profile = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()
        if not style_profile:
            # Create default style profile
            style_profile = StyleProfile(
                user_id=user_id,
                language="ko",
                tone="technical",
                blog_structure=["Summary", "What I did", "Learned", "Next"],
                report_structure=["Summary", "What I did", "Learned", "Next"],
                extra_instructions=None
            )
            db.add(style_profile)
            db.commit()
            db.refresh(style_profile)
        
        # Generate content
        from merge_forge.weekly_report import generate_weekly_report
        content = generate_weekly_report(user, weekly_summary, style_profile)
        
        # Save generated content
        generated = GeneratedContent(
            user_id=user_id,
            type="weekly_report",
            source_ref=f"weekly:{weekly_summary_id}",
            content=content
        )
        db.add(generated)
        db.commit()
        
        return {"status": "success", "user_id": user_id, "weekly_id": weekly_summary_id, "content_id": str(generated.id)}
    finally:
        db.close()


@celery_app.task
def generate_repo_blog_llm(user_id: str, repo_id: str):
    """Generate LLM-based repo blog post."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        repo = db.query(Repo).filter(Repo.id == repo_id).first()
        if not repo:
            return {"error": "Repo not found"}
        
        style_profile = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()
        if not style_profile:
            # Create default style profile
            style_profile = StyleProfile(
                user_id=user_id,
                language="ko",
                tone="technical",
                blog_structure=["Intro", "Problem", "Approach", "Result", "Next"],
                report_structure=["Summary", "What I did", "Learned", "Next"],
                extra_instructions=None
            )
            db.add(style_profile)
            db.commit()
            db.refresh(style_profile)
        
        # Generate content
        from merge_forge.repo_blog import generate_repo_blog
        content = generate_repo_blog(user, repo, style_profile)
        
        # Save generated content
        generated = GeneratedContent(
            user_id=user_id,
            type="repo_blog",
            source_ref=f"repo:{repo_id}",
            content=content
        )
        db.add(generated)
        db.commit()
        
        return {"status": "success", "user_id": user_id, "repo_id": repo_id, "content_id": str(generated.id)}
    finally:
        db.close()
