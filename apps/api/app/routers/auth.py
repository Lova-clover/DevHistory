from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from jose import jwt
import httpx

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.oauth_account import OAuthAccount

router = APIRouter()


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
    """Handle GitHub OAuth callback."""
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
    
    # Find or create user
    user = db.query(User).filter(User.email == github_user["email"]).first()
    if not user:
        user = User(
            email=github_user["email"],
            name=github_user.get("name") or github_user["login"],
            avatar_url=github_user.get("avatar_url"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
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
    
    # Create JWT token
    expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS)
    jwt_payload = {
        "sub": str(user.id),
        "exp": expire,
    }
    jwt_token = jwt.encode(jwt_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    
    # Set cookie and redirect to frontend
    response = RedirectResponse(url=f"{settings.FRONTEND_URL}/dashboard")
    response.set_cookie(
        key="access_token",
        value=jwt_token,
        httponly=True,
        max_age=settings.JWT_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
    )
    
    return response


@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookie."""
    response.delete_cookie(key="access_token")
    return {"message": "Logged out successfully"}
