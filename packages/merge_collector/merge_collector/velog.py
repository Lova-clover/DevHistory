"""Velog data collection via RSS."""
import httpx
import feedparser
from sqlalchemy.orm import Session
from typing import List, Dict, Any


async def sync_blog_posts(user_id: str, velog_id: str, db: Session) -> List[Dict[str, Any]]:
    """
    Sync Velog blog posts via RSS feed.
    
    Args:
        user_id: User UUID
        velog_id: Velog user ID (e.g., '@username')
        db: Database session
        
    Returns:
        List of synced blog post data
    """
    # Clean velog_id (remove @ if present)
    clean_id = velog_id.lstrip("@")
    
    # Fetch RSS feed
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://velog.io/rss/@{clean_id}")
        rss_content = response.text
    
    # Parse RSS
    feed = feedparser.parse(rss_content)
    
    posts = []
    for entry in feed.entries:
        post_data = {
            "external_id": entry.get("id", ""),
            "url": entry.get("link", ""),
            "title": entry.get("title", ""),
            "published_at": entry.get("published", ""),
        }
        posts.append(post_data)
    
    # TODO: Implement database upsert logic
    # from app.models.blog_post import BlogPost
    
    return posts
