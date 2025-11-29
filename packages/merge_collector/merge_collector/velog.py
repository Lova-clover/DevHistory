"""Velog data collection via RSS."""
import httpx
import feedparser
from datetime import datetime
from dateutil import parser
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
    
    # Upsert blog posts into database
    from app.models.blog_post import BlogPost
    
    synced_posts = []
    for post_data in posts:
        # Check if post exists
        existing_post = db.query(BlogPost).filter(
            BlogPost.user_id == user_id,
            BlogPost.external_id == post_data["external_id"]
        ).first()
        
        if not existing_post:
            # Parse published date
            try:
                published_at = parser.parse(post_data["published_at"])
            except:
                published_at = datetime.utcnow()
            
            # Create new blog post
            new_post = BlogPost(
                user_id=user_id,
                platform="velog",
                external_id=post_data["external_id"],
                url=post_data["url"],
                title=post_data["title"],
                published_at=published_at
            )
            db.add(new_post)
            synced_posts.append(new_post)
    
    db.commit()
    return [{
        "id": str(post.id),
        "title": post.title,
        "url": post.url,
        "published_at": post.published_at.isoformat()
    } for post in synced_posts]
