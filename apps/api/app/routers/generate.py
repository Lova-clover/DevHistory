from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.deps import get_current_user
from app.models.user import User
from app.models.weekly_summary import WeeklySummary
from app.models.repo import Repo
from app.models.generated_content import GeneratedContent

router = APIRouter()


@router.post("/weekly-report/{weekly_id}")
async def generate_weekly_report(
    weekly_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate LLM-based weekly report."""
    summary = db.query(WeeklySummary).filter(
        WeeklySummary.id == weekly_id,
        WeeklySummary.user_id == current_user.id
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Weekly summary not found")
    
    # TODO: Implement MergeForge LLM generation
    # from merge_forge import generate_weekly_report
    # content = generate_weekly_report(user, summary, style_profile)
    
    # Placeholder content
    content = f"""# 주간 개발 리포트 ({summary.week_start} ~ {summary.week_end})

## 📊 이번 주 활동 요약
- 커밋: {summary.commit_count}개
- 문제 풀이: {summary.problem_count}개
- 노트: {summary.note_count}개

## 💻 주요 활동

[LLM이 생성할 내용]

## 🎯 다음 주 목표

[LLM이 생성할 내용]
"""
    
    # Save to database
    summary.llm_summary = content
    
    generated = GeneratedContent(
        user_id=current_user.id,
        type="weekly_blog",
        source_ref=f"weekly:{weekly_id}",
        title=f"주간 리포트 {summary.week_start} ~ {summary.week_end}",
        content=content,
    )
    db.add(generated)
    db.commit()
    
    return {
        "id": str(generated.id),
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
    }


@router.post("/repo-blog/{repo_id}")
async def generate_repo_blog(
    repo_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate blog post draft for a repository."""
    repo = db.query(Repo).filter(
        Repo.id == repo_id,
        Repo.user_id == current_user.id
    ).first()
    
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # TODO: Implement MergeForge LLM generation
    # from merge_forge import generate_repo_blog
    # content = generate_repo_blog(user, repo, style_profile)
    
    # Placeholder content
    content = f"""# {repo.full_name}

## 프로젝트 소개
{repo.description or '[설명 없음]'}

## 기술 스택
- 주 언어: {repo.language or '정보 없음'}

## 주요 기능

[LLM이 생성할 내용]

## 개발 과정

[LLM이 생성할 내용]

## 배운 점

[LLM이 생성할 내용]

🔗 [GitHub에서 보기]({repo.html_url})
"""
    
    # Save to database
    generated = GeneratedContent(
        user_id=current_user.id,
        type="repo_blog",
        source_ref=f"repo:{repo_id}",
        title=f"{repo.full_name} 프로젝트 회고",
        content=content,
    )
    db.add(generated)
    db.commit()
    
    return {
        "id": str(generated.id),
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
    }
