from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from jose import jwt
import httpx
import logging

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.oauth_account import OAuthAccount
from app.deps import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def _set_auth_cookie(response: Response, jwt_token: str) -> None:
    """Set httpOnly secure auth cookie."""
    max_age = settings.JWT_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        path="/",
        max_age=max_age,
        domain=settings.COOKIE_DOMAIN or None,
    )


@router.get("/github/login")
async def github_login():
    """Redirect to GitHub OAuth authorization page."""
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}"
        f"&scope=user:email,repo"
    )
    return RedirectResponse(url=github_auth_url)


@router.get("/github/callback")
async def github_callback(code: str, db: Session = Depends(get_db)):
    """Handle GitHub OAuth callback. Sets httpOnly cookie and redirects."""
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Failed to get access token")
        
        # Get user info from GitHub
        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        github_user = user_response.json()
        
        # Get user emails from GitHub (separate API call)
        emails_response = await client.get(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        emails = emails_response.json()
        
        # Find primary email or first verified email
        email = github_user.get("email")
        if not email and isinstance(emails, list):
            for email_data in emails:
                if email_data.get("primary") and email_data.get("verified"):
                    email = email_data.get("email")
                    break
            if not email:
                for email_data in emails:
                    if email_data.get("verified"):
                        email = email_data.get("email")
                        break
        
        # Use login as fallback for email (GitHub username)
        if not email:
            email = f"{github_user['login']}@users.noreply.github.com"
    
    github_username = github_user.get("login", "")
    
    # Find or create user
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            name=github_user.get("name") or github_user["login"],
            avatar_url=github_user.get("avatar_url"),
            github_username=github_username,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update github_username and avatar if changed
        if github_username and user.github_username != github_username:
            user.github_username = github_username
        if github_user.get("avatar_url") and user.avatar_url != github_user["avatar_url"]:
            user.avatar_url = github_user["avatar_url"]
        user.updated_at = datetime.utcnow()
        db.commit()
    
    # Find or create OAuth account
    oauth_account = db.query(OAuthAccount).filter(
        OAuthAccount.provider == "github",
        OAuthAccount.provider_user_id == str(github_user["id"]),
    ).first()
    
    if oauth_account:
        oauth_account.access_token = access_token
        oauth_account.updated_at = datetime.utcnow()
    else:
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider="github",
            provider_user_id=str(github_user["id"]),
            access_token=access_token,
        )
        db.add(oauth_account)
    
    db.commit()

    # Queue GitHub sync on successful login (non-blocking for auth flow).
    try:
        from worker.tasks.sync_github import sync_github_for_user
        sync_github_for_user.delay(str(user.id))
    except Exception as exc:
        logger.warning("Failed to queue GitHub sync for user %s: %s", user.id, exc)
    
    # Create JWT token
    expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS)
    jwt_payload = {
        "sub": str(user.id),
        "exp": expire,
    }
    jwt_token = jwt.encode(jwt_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    # Set httpOnly cookie and redirect (NO token in URL)
    response = RedirectResponse(
        url=f"{settings.FRONTEND_URL}/auth/callback",
        status_code=302,
    )
    _set_auth_cookie(response, jwt_token)
    
    return response


@router.get("/me")
async def auth_me(current_user: User = Depends(get_current_user)):
    """Check auth status. Returns current user if cookie is valid."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url,
        "github_username": current_user.github_username,
    }


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing httpOnly cookie."""
    response.delete_cookie(
        key="access_token",
        path="/",
        domain=settings.COOKIE_DOMAIN or None,
    )
    return {"message": "Logged out successfully"}
