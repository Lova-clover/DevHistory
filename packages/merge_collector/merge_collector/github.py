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
    
    # Upsert repos into database
    from app.models.repo import Repo
    
    synced_repos = []
    for repo_data in repos:
        # Check if repo exists
        existing_repo = db.query(Repo).filter(
            Repo.user_id == user_id,
            Repo.provider_repo_id == str(repo_data["id"])
        ).first()
        
        if existing_repo:
            # Update existing repo
            existing_repo.full_name = repo_data["full_name"]
            existing_repo.html_url = repo_data["html_url"]
            existing_repo.description = repo_data.get("description")
            existing_repo.language = repo_data.get("language")
            existing_repo.stars = repo_data.get("stargazers_count", 0)
            existing_repo.forks = repo_data.get("forks_count", 0)
            existing_repo.is_fork = repo_data.get("fork", False)
            existing_repo.last_synced_at = datetime.utcnow()
            existing_repo.updated_at = datetime.utcnow()
            synced_repos.append(existing_repo)
        else:
            # Create new repo
            new_repo = Repo(
                user_id=user_id,
                provider_repo_id=str(repo_data["id"]),
                full_name=repo_data["full_name"],
                html_url=repo_data["html_url"],
                description=repo_data.get("description"),
                language=repo_data.get("language"),
                stars=repo_data.get("stargazers_count", 0),
                forks=repo_data.get("forks_count", 0),
                is_fork=repo_data.get("fork", False),
                last_synced_at=datetime.utcnow()
            )
            db.add(new_repo)
            synced_repos.append(new_repo)
    
    db.commit()
    return [{
        "id": str(repo.id),
        "full_name": repo.full_name,
        "html_url": repo.html_url,
        "language": repo.language
    } for repo in synced_repos]


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
    
    # Get repo from database
    from app.models.repo import Repo
    from app.models.commit import Commit
    
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        return []
    
    # Call GitHub API for commits
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{repo.full_name}/commits",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3+json",
            },
            params={
                "since": since_iso,
                "per_page": 100,
            }
        )
        commits_data = response.json()
    
    # Upsert commits into database
    synced_commits = []
    for commit_data in commits_data:
        commit_info = commit_data.get("commit", {})
        
        # Check if commit exists
        existing_commit = db.query(Commit).filter(
            Commit.repo_id == repo_id,
            Commit.sha == commit_data["sha"]
        ).first()
        
        if not existing_commit:
            # Parse commit date
            committed_at_str = commit_info.get("committer", {}).get("date")
            committed_at = datetime.fromisoformat(committed_at_str.replace("Z", "+00:00")) if committed_at_str else datetime.utcnow()
            
            # Create new commit
            new_commit = Commit(
                repo_id=repo_id,
                user_id=user_id,
                sha=commit_data["sha"],
                message=commit_info.get("message", ""),
                committed_at=committed_at,
                raw_data=commit_data
            )
            db.add(new_commit)
            synced_commits.append(new_commit)
    
    db.commit()
    return [{
        "sha": commit.sha,
        "message": commit.message,
        "committed_at": commit.committed_at.isoformat()
    } for commit in synced_commits]
