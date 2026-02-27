"""Coding coach – problem analysis, quiz, advice based on solved.ac data."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
import time

from app.deps import get_current_user, get_db
from app.models.user import User
from app.models.problem import Problem
from app.models.generated_content import GeneratedContent

router = APIRouter()


class QuizRequest(BaseModel):
    topic: Optional[str] = ""


@router.get("/stats")
async def get_problem_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get solved.ac problem statistics for the current user."""
    problems = db.query(Problem).filter(Problem.user_id == current_user.id).all()
    if not problems:
        return {"total": 0, "by_level": {}, "by_tag": {}, "recent": []}

    by_level = {}
    by_tag = {}
    for p in problems:
        lvl = p.level or 0
        by_level[lvl] = by_level.get(lvl, 0) + 1
        for tag in (p.tags or []):
            by_tag[tag] = by_tag.get(tag, 0) + 1

    sorted_tags = sorted(by_tag.items(), key=lambda x: x[1], reverse=True)
    weak_tags = [t for t, c in sorted(by_tag.items(), key=lambda x: x[1]) if c <= 2][:10]

    recent = sorted(problems, key=lambda x: x.solved_at or x.created_at, reverse=True)[:10]

    return {
        "total": len(problems),
        "by_level": dict(sorted(by_level.items())),
        "by_tag": dict(sorted_tags[:15]),
        "weak_tags": weak_tags,
        "recent": [
            {
                "problem_id": p.problem_id,
                "title": p.title,
                "level": p.level,
                "tags": p.tags or [],
                "solved_at": p.solved_at.isoformat() if p.solved_at else None,
            }
            for p in recent
        ],
    }


@router.post("/analyze")
async def analyze_problems(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run AI analysis on user's problem solving patterns."""
    total = db.query(func.count(Problem.id)).filter(Problem.user_id == current_user.id).scalar() or 0
    if total == 0:
        raise HTTPException(400, "Solved.ac 문제 데이터가 없습니다. 먼저 동기화해주세요.")

    from worker.tasks.forge_llm import generate_coach_analysis
    task = generate_coach_analysis.delay(str(current_user.id))

    max_wait = 30
    start = time.time()
    while time.time() - start < max_wait:
        if task.ready():
            result = task.get()
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "analysis": result.get("analysis"),
                    "content_id": result.get("content_id"),
                }
            raise HTTPException(500, result.get("error", "Analysis failed"))
        time.sleep(0.5)

    return {"status": "processing", "message": "분석이 진행 중입니다."}


@router.post("/quiz")
async def generate_quiz(
    request: QuizRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a coding quiz targeting weak areas."""
    from worker.tasks.forge_llm import generate_coach_quiz
    task = generate_coach_quiz.delay(str(current_user.id), request.topic or "")

    max_wait = 30
    start = time.time()
    while time.time() - start < max_wait:
        if task.ready():
            result = task.get()
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "quiz": result.get("quiz"),
                    "content_id": result.get("content_id"),
                }
            raise HTTPException(500, result.get("error", "Quiz generation failed"))
        time.sleep(0.5)

    return {"status": "processing", "message": "퀴즈를 생성 중입니다."}


@router.get("/history")
async def get_coach_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get previous coaching analyses and quizzes."""
    contents = (
        db.query(GeneratedContent)
        .filter(
            GeneratedContent.user_id == current_user.id,
            GeneratedContent.content_type.in_(["coach_analysis", "coach_quiz"]),
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
