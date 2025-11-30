"""GitHub data collection."""
import httpx
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.utils.retry import retry_with_backoff, handle_api_errors, github_rate_limiter
from app.exceptions import DataValidationError

logger = logging.getLogger(__name__)


@handle_api_errors("GitHub")
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
    # Apply rate limiting
    await github_rate_limiter.acquire()
    
    async def fetch_repos():
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                params={
                    "affiliation": "owner",  # Only repos owned by the user
                    "sort": "updated",
                    "per_page": 100,
                }
            )
            response.raise_for_status()
            return response.json()
    
    repos = await retry_with_backoff(fetch_repos)
    
    # Validate and upsert repos into database
    from app.models.repo import Repo
    
    if not isinstance(repos, list):
        raise DataValidationError("GitHub API returned invalid data format")
    
    synced_repos = []
    for repo_data in repos:
        # Validate required fields
        if not all(key in repo_data for key in ["id", "full_name", "html_url"]):
            logger.warning(f"Skipping repo with missing fields: {repo_data.get('id', 'unknown')}")
            continue
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
            # Update created_at from GitHub if available
            if repo_data.get("created_at"):
                try:
                    existing_repo.created_at = datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
            # Use GitHub's updated_at if available, otherwise use current time
            if repo_data.get("updated_at"):
                try:
                    existing_repo.updated_at = datetime.fromisoformat(repo_data["updated_at"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    existing_repo.updated_at = datetime.utcnow()
            synced_repos.append(existing_repo)
        else:
            # Create new repo - use GitHub's created_at and updated_at
            created_at = datetime.utcnow()
            updated_at = datetime.utcnow()
            
            if repo_data.get("created_at"):
                try:
                    created_at = datetime.fromisoformat(repo_data["created_at"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
            
            if repo_data.get("updated_at"):
                try:
                    updated_at = datetime.fromisoformat(repo_data["updated_at"].replace("Z", "+00:00"))
                except (ValueError, AttributeError):
                    pass
            
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
                last_synced_at=datetime.utcnow(),
                created_at=created_at,
                updated_at=updated_at
            )
            db.add(new_repo)
            synced_repos.append(new_repo)
    
    db.commit()
    logger.info(f"Successfully synced {len(synced_repos)} repos for user {user_id}")
    
    return [{
        "id": str(repo.id),
        "full_name": repo.full_name,
        "html_url": repo.html_url,
        "language": repo.language
    } for repo in synced_repos]


@handle_api_errors("GitHub")
async def sync_commits(
    user_id: str,
    repo_id: str,
    access_token: str,
    db: Session,
    since_days: int | None = None
) -> List[Dict[str, Any]]:
    """
    Sync commits for a specific repository.
    
    Args:
        user_id: User UUID
        repo_id: Repository UUID
        access_token: GitHub OAuth access token
        db: Database session
        since_days: Number of days to look back (None = all commits)
        
    Returns:
        List of synced commit data
    """
    # Build params
    params = {"per_page": 100}
    if since_days is not None:
        since = datetime.utcnow() - timedelta(days=since_days)
        params["since"] = since.isoformat() + "Z"
    
    # Get repo from database
    from app.models.repo import Repo
    from app.models.commit import Commit
    from app.exceptions import ResourceNotFoundError
    
    repo = db.query(Repo).filter(Repo.id == repo_id).first()
    if not repo:
        raise ResourceNotFoundError("Repository", repo_id)
    
    # Fetch all commits with pagination
    all_commits = []
    page = 1
    
    while True:
        # Apply rate limiting
        await github_rate_limiter.acquire()
        
        # Call GitHub API for commits
        async def fetch_commits():
            async with httpx.AsyncClient(timeout=30.0) as client:
                page_params = {**params, "page": page}
                response = await client.get(
                    f"https://api.github.com/repos/{repo.full_name}/commits",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    params=page_params
                )
                response.raise_for_status()
                return response.json()
        
        commits_data = await retry_with_backoff(fetch_commits)
        
        if not commits_data:
            break
            
        all_commits.extend(commits_data)
        
        # If we got less than per_page, we've reached the end
        if len(commits_data) < 100:
            break
            
        page += 1
    
    commits_data = all_commits
    
    # Upsert commits into database
    synced_commits = []
    for commit_data in commits_data:
        # Validate required fields
        if not all(key in commit_data for key in ["sha", "commit"]):
            logger.warning(f"Skipping commit with missing fields")
            continue
        
        commit_info = commit_data.get("commit", {})
        
        # Check if commit exists
        existing_commit = db.query(Commit).filter(
            Commit.repo_id == repo_id,
            Commit.sha == commit_data["sha"]
        ).first()
        
        if not existing_commit:
            # Parse commit date with error handling
            committed_at_str = commit_info.get("committer", {}).get("date")
            try:
                committed_at = datetime.fromisoformat(committed_at_str.replace("Z", "+00:00")) if committed_at_str else datetime.utcnow()
            except (ValueError, AttributeError):
                logger.warning(f"Invalid commit date format: {committed_at_str}")
                committed_at = datetime.utcnow()
            
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
    logger.info(f"Successfully synced {len(synced_commits)} commits for repo {repo.full_name}")
    
    return [{
        "sha": commit.sha,
        "message": commit.message,
        "committed_at": commit.committed_at.isoformat()
    } for commit in synced_commits]
