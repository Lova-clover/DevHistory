"""Resume and cover letter generation from portfolio data."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import time

from app.deps import get_current_user, get_db
from app.models.user import User
from app.models.generated_content import GeneratedContent

router = APIRouter()


class ResumeRequest(BaseModel):
    resume_type: str = "resume"  # 'resume' or 'cover_letter'
    extra_context: Optional[str] = ""


@router.post("/generate")
async def generate_resume(
    request: ResumeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a resume or cover letter from portfolio data."""
    if request.resume_type not in ("resume", "cover_letter"):
        raise HTTPException(400, "resume_type must be 'resume' or 'cover_letter'")

    from worker.tasks.forge_llm import generate_resume as gen_resume_task
    task = gen_resume_task.delay(
        str(current_user.id), request.resume_type, request.extra_context or ""
    )

    max_wait = 45
    start = time.time()
    while time.time() - start < max_wait:
        if task.ready():
            result = task.get()
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "content": result.get("content"),
                    "content_id": result.get("content_id"),
                }
            raise HTTPException(500, result.get("error", "Generation failed"))
        time.sleep(0.5)

    return {"status": "processing", "message": "생성 중입니다. 잠시 후 콘텐츠 페이지에서 확인해주세요."}


@router.get("/history")
async def get_resume_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get previously generated resumes and cover letters."""
    contents = (
        db.query(GeneratedContent)
        .filter(
            GeneratedContent.user_id == current_user.id,
            GeneratedContent.content_type.in_(["resume", "cover_letter"]),
        )
        .order_by(GeneratedContent.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": str(c.id),
            "type": c.content_type,
            "title": c.title,
            "content": c.content,
            "created_at": c.created_at.isoformat(),
        }
        for c in contents
    ]
