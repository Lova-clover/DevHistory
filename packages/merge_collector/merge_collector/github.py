"""GitHub data collection."""
import httpx
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Any


async def sync_repos(user_id: str, access_token: str, db: Session) -> List[Dict[str, Any]]:
    """
    Sync user's GitHub repositories.
    
    Args:
        user_id: User UUID
        access_token: GitHub OAuth access token
        db: Database session
        
    Returns:
        List of synced repo data
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            params={
                "sort": "updated",
                "per_page": 100,
            }
        )
        repos = response.json()
    
    # TODO: Implement actual database upsert logic
    # from app.models.repo import Repo
    # for repo_data in repos:
    #     upsert repo into database
    
    return repos


async def sync_commits(
    user_id: str,
    repo_id: str,
    access_token: str,
    db: Session,
    since_days: int = 30
) -> List[Dict[str, Any]]:
    """
    Sync commits for a specific repository.
    
    Args:
        user_id: User UUID
        repo_id: Repository UUID
        access_token: GitHub OAuth access token
        db: Database session
        since_days: Number of days to look back
        
    Returns:
        List of synced commit data
    """
    since = datetime.utcnow() - timedelta(days=since_days)
    since_iso = since.isoformat() + "Z"
    
    # TODO: Implement actual GitHub API call and database upsert
    # 1. Get repo full_name from database
    # 2. Call GitHub API for commits
    # 3. Upsert commits into database
    
    return []
