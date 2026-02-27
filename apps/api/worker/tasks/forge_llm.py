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
from app.models.llm_credential import LlmCredential
from app.crypto import decrypt_value
from datetime import datetime


def _get_user_llm_key(db, user_id: str) -> tuple[str | None, str]:
    """Return (api_key, model) for a user. Falls back to None (env var)."""
    cred = db.query(LlmCredential).filter(LlmCredential.user_id == user_id).first()
    if cred and cred.encrypted_api_key:
        try:
            api_key = decrypt_value(cred.encrypted_api_key)
            cred.last_used_at = datetime.utcnow()
            db.commit()
            return api_key, cred.model or "gpt-4o-mini"
        except Exception:
            pass
    return None, "gpt-4o-mini"


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
        
        api_key, model = _get_user_llm_key(db, user_id)

        from merge_forge.weekly_report import generate_weekly_report
        content = generate_weekly_report(user, weekly_summary, style_profile, api_key=api_key, model=model)
        
        generated = GeneratedContent(
            user_id=user_id,
            content_type="weekly_report",
            source_ref=f"weekly:{weekly_summary_id}",
            content=content,
            status="completed",
        )
        db.add(generated)
        db.commit()
        
        return {"status": "success", "user_id": user_id, "weekly_id": weekly_summary_id, "content_id": str(generated.id)}
    except Exception as e:
        return {"error": str(e)}
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
        
        api_key, model = _get_user_llm_key(db, user_id)

        from merge_forge.repo_blog import generate_repo_blog
        content = generate_repo_blog(user, repo, style_profile, api_key=api_key, model=model)
        
        generated = GeneratedContent(
            user_id=user_id,
            content_type="repo_blog",
            source_ref=f"repo:{repo_id}",
            content=content,
            status="completed",
        )
        db.add(generated)
        db.commit()
        
        return {"status": "success", "user_id": user_id, "repo_id": repo_id, "content_id": str(generated.id)}
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()
