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
from app.schemas.content import (
    ContentGenerateRequest,
    ContentResponse,
    ContentListResponse,
    ContentUpdateRequest,
    ContentRegenerateRequest,
    ContentFilterRequest,
    ContentStatsResponse
)

router = APIRouter()


@router.post("/content", response_model=ContentResponse)
async def generate_content(
    request: ContentGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate content using LLM based on user's activity data."""
    # Create content record
    content = GeneratedContent(
        user_id=current_user.id,
        content_type=request.content_type,
        title=request.title or f"Generated {request.content_type}",
        content="",  # Will be filled by worker
        status="pending",
        metadata={
            "context": request.context,
            "date_range_start": request.date_range_start.isoformat() if request.date_range_start else None,
            "date_range_end": request.date_range_end.isoformat() if request.date_range_end else None,
            "use_style_profile": request.use_style_profile
        }
    )
    db.add(content)
    db.commit()
    db.refresh(content)
    
    # Trigger LLM generation task
    from worker.tasks.forge_llm import generate_content_llm
    task = generate_content_llm.delay(str(current_user.id), str(content.id))
    
    return ContentResponse.model_validate(content)


@router.get("/contents")
async def get_generated_contents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all generated contents for current user."""
    contents = db.query(GeneratedContent).filter(
        GeneratedContent.user_id == current_user.id
    ).order_by(GeneratedContent.created_at.desc()).all()
    
    return [{
        "id": str(content.id),
        "type": content.content_type,
        "source_ref": content.source_ref,
        "title": content.title,
        "content": content.content,
        "status": content.status,
        "created_at": content.created_at.isoformat()
    } for content in contents]


@router.get("/content", response_model=ContentListResponse)
async def list_generated_content(
    filter_request: ContentFilterRequest = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all generated content with optional filters."""
    query = db.query(GeneratedContent).filter(GeneratedContent.user_id == current_user.id)
    
    if filter_request.content_type:
        query = query.filter(GeneratedContent.content_type == filter_request.content_type)
    if filter_request.status:
        query = query.filter(GeneratedContent.status == filter_request.status)
    if filter_request.start_date:
        query = query.filter(GeneratedContent.created_at >= filter_request.start_date)
    if filter_request.end_date:
        query = query.filter(GeneratedContent.created_at <= filter_request.end_date)
    
    total = query.count()
    contents = query.order_by(GeneratedContent.created_at.desc()).offset(
        (filter_request.page - 1) * filter_request.page_size
    ).limit(filter_request.page_size).all()
    
    return ContentListResponse(
        contents=[ContentResponse.model_validate(c) for c in contents],
        total=total,
        page=filter_request.page,
        page_size=filter_request.page_size
    )


@router.post("/weekly-report/{weekly_id}", deprecated=True)
async def generate_weekly_report(
    weekly_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate LLM-based weekly report. (Deprecated: Use /content endpoint)"""
    summary = db.query(WeeklySummary).filter(
        WeeklySummary.id == weekly_id,
        WeeklySummary.user_id == current_user.id
    ).first()
    
    if not summary:
        raise HTTPException(status_code=404, detail="Weekly summary not found")
    
    # Trigger LLM generation task
    from worker.tasks.forge_llm import generate_weekly_report_llm
    task = generate_weekly_report_llm.delay(str(current_user.id), str(weekly_id))
    
    return {
        "message": "Weekly report generation started",
        "task_id": task.id,
        "status": "processing"
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
    
    # Trigger LLM generation task for repo blog
    from worker.tasks.forge_llm import generate_repo_blog_llm
    task = generate_repo_blog_llm.delay(str(current_user.id), str(repo_id))
    
    # Wait for task to complete (with timeout)
    import time
    max_wait = 30  # 30 seconds
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        if task.ready():
            result = task.get()
            if result.get("status") == "success":
                # Fetch the generated content
                content = db.query(GeneratedContent).filter(
                    GeneratedContent.id == result.get("content_id")
                ).first()
                if content:
                    return {
                        "message": "Blog generated successfully",
                        "content": content.content,
                        "content_id": str(content.id)
                    }
            break
        time.sleep(0.5)
    
    return {
        "message": "Repository blog generation started",
        "task_id": task.id,
        "status": "processing"
    }


@router.put("/content/{content_id}", response_model=ContentResponse)
async def update_content(
    content_id: UUID,
    request: ContentUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update generated content."""
    content = db.query(GeneratedContent).filter(
        GeneratedContent.id == content_id,
        GeneratedContent.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    if request.title is not None:
        content.title = request.title
    if request.content is not None:
        content.content = request.content
    if request.metadata is not None:
        content.metadata = request.metadata
    
    content.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(content)
    
    return ContentResponse.model_validate(content)


@router.post("/content/{content_id}/regenerate", response_model=ContentResponse)
async def regenerate_content(
    content_id: UUID,
    request: ContentRegenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Regenerate content with optionally updated context."""
    content = db.query(GeneratedContent).filter(
        GeneratedContent.id == content_id,
        GeneratedContent.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    # Update context if provided
    if request.new_context:
        if not content.metadata:
            content.metadata = {}
        content.metadata["context"] = request.new_context
        content.metadata["use_style_profile"] = request.use_style_profile
    
    content.status = "pending"
    content.updated_at = datetime.utcnow()
    db.commit()
    
    # Trigger regeneration
    from worker.tasks.forge_llm import generate_content_llm
    task = generate_content_llm.delay(str(current_user.id), str(content.id))
    
    return ContentResponse.model_validate(content)


@router.get("/content/{content_id}", response_model=ContentResponse)
async def get_content(
    content_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific generated content."""
    content = db.query(GeneratedContent).filter(
        GeneratedContent.id == content_id,
        GeneratedContent.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return ContentResponse.model_validate(content)


@router.delete("/content/{content_id}")
async def delete_content(
    content_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete generated content."""
    content = db.query(GeneratedContent).filter(
        GeneratedContent.id == content_id,
        GeneratedContent.user_id == current_user.id
    ).first()
    
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")
    
    db.delete(content)
    db.commit()
    
    return {"message": "Content deleted successfully"}


@router.get("/stats", response_model=ContentStatsResponse)
async def get_content_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get content generation statistics."""
    from sqlalchemy import func
    
    total = db.query(func.count(GeneratedContent.id)).filter(
        GeneratedContent.user_id == current_user.id
    ).scalar() or 0
    
    # Count by type
    by_type_raw = db.query(
        GeneratedContent.content_type,
        func.count(GeneratedContent.id)
    ).filter(
        GeneratedContent.user_id == current_user.id
    ).group_by(GeneratedContent.content_type).all()
    by_type = {ct: count for ct, count in by_type_raw}
    
    # Count by status
    by_status_raw = db.query(
        GeneratedContent.status,
        func.count(GeneratedContent.id)
    ).filter(
        GeneratedContent.user_id == current_user.id
    ).group_by(GeneratedContent.status).all()
    by_status = {status: count for status, count in by_status_raw}
    
    # Calculate success rate
    completed = by_status.get("completed", 0)
    failed = by_status.get("failed", 0)
    success_rate = (completed / (completed + failed) * 100) if (completed + failed) > 0 else 0
    
    return ContentStatsResponse(
        total_generated=total,
        by_type=by_type,
        by_status=by_status,
        success_rate=round(success_rate, 2),
        average_generation_time=None  # TODO: Calculate from metadata
    )
