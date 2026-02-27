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


@celery_app.task
def generate_content_llm(user_id: str, content_id: str):
    """Generic content generation task (used by POST /content and /regenerate)."""
    db = SessionLocal()
    try:
        content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
        if not content:
            return {"error": "Content record not found"}

        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            content.status = "failed"
            content.error_message = "User not found"
            db.commit()
            return {"error": "User not found"}

        # Mark as generating
        content.status = "generating"
        content.started_at = datetime.utcnow()
        db.commit()

        # Read metadata stored by the router
        meta = content.metadata or {}
        context_text = meta.get("context") or ""
        use_style = meta.get("use_style_profile", True)
        date_start = meta.get("date_range_start")
        date_end = meta.get("date_range_end")

        # Resolve style profile if requested
        style_profile = None
        if use_style:
            style_profile = db.query(StyleProfile).filter(StyleProfile.user_id == user_id).first()

        # Build LLM prompts
        system_prompt = _build_content_system_prompt(content.content_type, style_profile)
        user_prompt = _build_content_user_prompt(
            content.content_type, content.title, context_text, date_start, date_end
        )

        # Resolve API key (BYO or fallback)
        api_key, model = _get_user_llm_key(db, user_id)

        from merge_core.llm import generate_text
        generated_text = generate_text(
            system_prompt, user_prompt, model=model, api_key=api_key
        )

        now = datetime.utcnow()
        content.content = generated_text
        content.status = "completed"
        content.updated_at = now
        content.completed_at = now
        if content.started_at:
            content.generation_seconds = (now - content.started_at).total_seconds()
        db.commit()

        return {"status": "success", "content_id": content_id}
    except Exception as e:
        # Best-effort: mark failed
        try:
            content = db.query(GeneratedContent).filter(GeneratedContent.id == content_id).first()
            if content:
                content.status = "failed"
                content.error_message = str(e)[:2000]
                content.updated_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
        return {"error": str(e)}
    finally:
        db.close()


# ── Prompt helpers for generic content generation ────────────────

def _build_content_system_prompt(content_type: str, style_profile=None) -> str:
    parts = [
        "너는 사용자의 개발 활동을 멋진 글로 정리해주는 AI 편집자다.",
        f"생성할 콘텐츠 유형: {content_type}",
    ]
    if style_profile:
        parts.append(f"출력 언어: {style_profile.language}")
        parts.append(f"톤: {style_profile.tone}")
        if content_type in ("blog_post",) and style_profile.blog_structure:
            parts.append("글 구조: " + " > ".join(style_profile.blog_structure))
        if content_type in ("report", "summary") and style_profile.report_structure:
            parts.append("리포트 구조: " + " > ".join(style_profile.report_structure))
        if style_profile.extra_instructions:
            parts.append(f"추가 지침: {style_profile.extra_instructions}")
    else:
        parts.append("출력 언어: ko")
        parts.append("톤: technical")
    return "\n".join(parts)


def _build_content_user_prompt(
    content_type: str, title: str, context: str,
    date_start: str | None, date_end: str | None,
) -> str:
    lines = []
    if title:
        lines.append(f"제목: {title}")
    if date_start or date_end:
        lines.append(f"기간: {date_start or '?'} ~ {date_end or '?'}")
    if context:
        lines.append(f"참고 맥락 / 추가 지시:\n{context}")
    lines.append("\n위 정보를 바탕으로 Markdown 형식의 글을 작성해줘.")
    return "\n".join(lines)
