"""solved.ac data collection."""
import httpx
import logging
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime
from app.utils.retry import retry_with_backoff, handle_api_errors, solvedac_rate_limiter
from app.exceptions import DataValidationError

logger = logging.getLogger(__name__)


@handle_api_errors("solved.ac")
async def sync_problems(user_id: str, handle: str, db: Session) -> List[Dict[str, Any]]:
    """
    Sync solved.ac problems for a user.
    
    Args:
        user_id: User UUID
        handle: solved.ac handle
        db: Database session
        
    Returns:
        List of synced problem data
    """
    # Get solved problems from solved.ac API
    # Note: solved.ac API documentation: https://solvedac.github.io/unofficial-documentation
    
    from app.models.problem import Problem
    
    # Fetch all problems with pagination
    all_problems = []
    page = 1
    
    async with httpx.AsyncClient() as client:
        while True:
            # Get user's solved problems (using search API)
            try:
                response = await client.get(
                    f"https://solved.ac/api/v3/search/problem",
                    params={
                        "query": f"solved_by:{handle}",
                        "sort": "solved",
                        "direction": "desc",
                        "page": page,
                        "limit": 100
                    }
                )
                search_result = response.json()
                items = search_result.get("items", [])
                
                if not items:
                    break
                
                all_problems.extend(items)
                
                # Check if we've reached the end
                total = search_result.get("count", 0)
                if len(all_problems) >= total:
                    break
                    
                page += 1
                
            except Exception as e:
                print(f"Error fetching solved.ac data: {e}")
                break
    
    problems_data = all_problems
    
    # Upsert problems into database
    synced_problems = []
    for problem_data in problems_data:
        # Validate required fields
        if "problemId" not in problem_data:
            logger.warning("Skipping problem with missing problemId")
            continue
        
        # Check if problem exists
        existing_problem = db.query(Problem).filter(
            Problem.user_id == user_id,
            Problem.problem_id == problem_data["problemId"]
        ).first()
        
        if not existing_problem:
            # Create new problem
            tags = [tag["key"] for tag in problem_data.get("tags", [])]
            
            new_problem = Problem(
                user_id=user_id,
                problem_id=problem_data["problemId"],
                title=problem_data.get("titleKo") or problem_data.get("title"),
                level=problem_data.get("level"),
                tags=tags,
                solved_at=datetime.utcnow(),  # Note: actual solve time not available from API
                raw_data=problem_data
            )
            db.add(new_problem)
            synced_problems.append(new_problem)
    
    db.commit()
    logger.info(f"Successfully synced {len(synced_problems)} problems for user {handle}")
    
    return [{
        "problem_id": problem.problem_id,
        "title": problem.title,
        "level": problem.level,
        "tags": problem.tags
    } for problem in synced_problems]
