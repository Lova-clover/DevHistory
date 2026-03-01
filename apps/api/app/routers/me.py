import secrets
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.deps import get_current_user, get_db
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.repo import Repo
from app.models.commit import Commit
from app.models.problem import Problem
from app.models.blog_post import BlogPost
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
from html import escape

router = APIRouter()


class UserResponse(BaseModel):
    id: str
    email: str
    name: str | None
    avatar_url: str | None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url,
    }


@router.get("/connections")
async def get_connections(current_user: User = Depends(get_current_user)):
    """Get user's connected accounts status."""
    return {
        "github": len([acc for acc in current_user.oauth_accounts if acc.provider == "github"]) > 0,
        "solvedac": current_user.user_profile.solvedac_handle if current_user.user_profile else None,
        "velog": current_user.user_profile.velog_id if current_user.user_profile else None,
    }


@router.get("/portfolio")
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's portfolio data aggregated from all sources."""
    
    # Get repos
    repos = db.query(Repo).filter(Repo.user_id == current_user.id).all()
    total_repos = len(repos)
    total_stars = sum(repo.stars or 0 for repo in repos)
    
    # Get commits - count directly from database
    total_commits = db.query(func.count(Commit.id)).filter(
        Commit.user_id == current_user.id
    ).scalar() or 0
    
    # Get problems
    total_problems = db.query(func.count(Problem.id)).filter(
        Problem.user_id == current_user.id
    ).scalar() or 0
    
    # Get blog posts
    total_blogs = db.query(func.count(BlogPost.id)).filter(
        BlogPost.user_id == current_user.id
    ).scalar() or 0
    
    # Language statistics
    language_stats = {}
    for repo in repos:
        if repo.language:
            language_stats[repo.language] = language_stats.get(repo.language, 0) + 1
    
    # Top languages by repository count
    language_repos = db.query(
        Repo.language,
        func.count(Repo.id).label("repo_count")
    ).filter(
        Repo.user_id == current_user.id,
        Repo.language.isnot(None)
    ).group_by(Repo.language).order_by(desc("repo_count")).limit(10).all()
    
    # Recent activity (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_commits = db.query(Commit).filter(
        Commit.user_id == current_user.id,
        Commit.committed_at >= thirty_days_ago
    ).count()
    
    # Calculate activity days (days with commits)
    activity_days = db.query(
        func.date(Commit.committed_at).label("date")
    ).filter(
        Commit.user_id == current_user.id
    ).distinct().count()
    
    # Top repositories by commit count
    from sqlalchemy import func as sql_func
    from app.models.user_profile import UserProfile
    
    # Get user profile settings
    user_profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    max_repos = user_profile.max_portfolio_repos if user_profile and user_profile.max_portfolio_repos else 6
    
    repo_commit_counts = db.query(
        Repo.id,
        sql_func.count(Commit.id).label('commit_count')
    ).join(Commit, Commit.repo_id == Repo.id).filter(
        Repo.user_id == current_user.id
    ).group_by(Repo.id).order_by(desc('commit_count')).limit(max_repos).all()
    
    top_repo_ids = [r.id for r in repo_commit_counts]
    top_repos = db.query(Repo).filter(Repo.id.in_(top_repo_ids)).all() if top_repo_ids else []
    # Sort by commit count order
    top_repos_dict = {repo.id: repo for repo in top_repos}
    top_repos = [top_repos_dict[repo_id] for repo_id in top_repo_ids if repo_id in top_repos_dict]
    
    # Get recent commits for activity feed
    recent_commit_list = db.query(Commit).filter(
        Commit.user_id == current_user.id
    ).order_by(desc(Commit.committed_at)).limit(10).all()
    
    # Get GitHub username from OAuth
    github_username = None
    for acc in current_user.oauth_accounts:
        if acc.provider == "github":
            # Try to extract username from provider_user_id or fetch from repos
            if repos:
                # Extract from first repo's full_name (format: username/repo)
                github_username = repos[0].full_name.split('/')[0] if '/' in repos[0].full_name else None
            break
    
    return {
        "user": {
            "id": str(current_user.id),
            "name": user_profile.portfolio_name if user_profile and user_profile.portfolio_name else current_user.name,
            "email": user_profile.portfolio_email if user_profile and user_profile.portfolio_email else current_user.email,
            "bio": user_profile.portfolio_bio if user_profile and user_profile.portfolio_bio else None,
            "avatar_url": current_user.avatar_url,
            "github_username": github_username,
        },
        "stats": {
            "total_repos": total_repos,
            "total_commits": total_commits,
            "total_problems": total_problems,
            "total_blogs": total_blogs,
            "total_stars": total_stars,
            "activity_days": activity_days,
            "recent_commits": recent_commits,
        },
        "languages": [
            {"name": lang, "count": count}
            for lang, count in language_repos
        ],
        "top_repos": [
            {
                "id": str(repo.id),
                "name": repo.full_name.split('/')[-1] if '/' in repo.full_name else repo.full_name,
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "stars": repo.stars or 0,
                "forks": repo.forks or 0,
                "html_url": repo.html_url,
            }
            for repo in top_repos
        ],
        "recent_activity": [
            {
                "id": str(commit.id),
                "type": "commit",
                "date": commit.committed_at.isoformat() if commit.committed_at else None,
                "message": commit.message,
                "repo_name": next((r.full_name for r in repos if r.id == commit.repo_id), "Unknown"),
            }
            for commit in recent_commit_list
        ]
    }


# ── Share Settings ───────────────────────────────────────────────

def _fmt_date(value: str | None) -> str:
    if not value:
        return "-"
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except Exception:
        return value


def _render_portfolio_pdf_html(portfolio: dict) -> str:
    user = portfolio.get("user", {})
    stats = portfolio.get("stats", {})
    languages = portfolio.get("languages", [])
    top_repos = portfolio.get("top_repos", [])
    recent_activity = portfolio.get("recent_activity", [])

    user_name = escape(user.get("name") or "Unknown User")
    user_email = escape(user.get("email") or "-")
    user_bio = escape(user.get("bio") or "")
    github_username = user.get("github_username") or ""
    avatar_url = user.get("avatar_url") or ""
    github_link = (
        f"https://github.com/{escape(github_username)}" if github_username else ""
    )

    language_rows = "\n".join(
        [
            f"""
            <tr>
              <td>{escape(lang.get("name") or "-")}</td>
              <td class="num">{lang.get("count") or 0}</td>
            </tr>
            """
            for lang in languages
        ]
    ) or '<tr><td colspan="2" class="muted">No language data</td></tr>'

    repo_cards = "\n".join(
        [
            f"""
            <article class="repo-card">
              <div class="repo-top">
                <h3>{escape(repo.get("name") or "-")}</h3>
                <span class="badge">★ {repo.get("stars") or 0}</span>
              </div>
              <p>{escape(repo.get("description") or "No description")}</p>
              <div class="repo-meta">
                <span>{escape(repo.get("language") or "-")}</span>
                <span>Forks {repo.get("forks") or 0}</span>
              </div>
              <div class="repo-url">{escape(repo.get("html_url") or "")}</div>
            </article>
            """
            for repo in top_repos
        ]
    ) or '<p class="muted">No repositories found.</p>'

    activity_rows = "\n".join(
        [
            f"""
            <tr>
              <td>{_fmt_date(item.get("date"))}</td>
              <td>{escape(item.get("repo_name") or "-")}</td>
              <td>{escape(item.get("message") or "-")}</td>
            </tr>
            """
            for item in recent_activity
        ]
    ) or '<tr><td colspan="3" class="muted">No recent activity</td></tr>'

    github_row = (
        f'<a href="{github_link}" target="_blank" rel="noopener noreferrer">{escape(github_link)}</a>'
        if github_link
        else "-"
    )

    avatar_html = (
        f'<img src="{escape(avatar_url)}" alt="avatar" class="avatar" />'
        if avatar_url
        else f'<div class="avatar-fallback">{escape((user.get("name") or "U")[:1].upper())}</div>'
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>DevHistory Portfolio</title>
  <style>
    @page {{
      size: A4;
      margin: 12mm;
    }}
    * {{
      box-sizing: border-box;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    body {{
      margin: 0;
      font-family: "Noto Sans KR", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
      color: #0f172a;
      background: #ffffff;
      font-size: 12px;
      line-height: 1.45;
    }}
    .page {{
      width: 100%;
      display: flex;
      flex-direction: column;
      gap: 14px;
    }}
    .header {{
      display: flex;
      gap: 14px;
      padding: 16px;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%);
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    .avatar, .avatar-fallback {{
      width: 88px;
      height: 88px;
      border-radius: 999px;
      object-fit: cover;
      flex: 0 0 auto;
    }}
    .avatar-fallback {{
      display: grid;
      place-items: center;
      background: #1d4ed8;
      color: white;
      font-size: 34px;
      font-weight: 700;
    }}
    .title h1 {{
      margin: 0;
      font-size: 24px;
      line-height: 1.2;
    }}
    .title .sub {{
      margin-top: 4px;
      color: #334155;
      font-size: 12px;
    }}
    .bio {{
      margin-top: 8px;
      color: #334155;
      white-space: pre-wrap;
    }}
    .links {{
      margin-top: 8px;
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      color: #0f172a;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
    }}
    .stat {{
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 10px;
      background: #fff;
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    .stat .k {{
      color: #475569;
      font-size: 11px;
    }}
    .stat .v {{
      margin-top: 4px;
      font-size: 20px;
      font-weight: 700;
    }}
    .section {{
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 14px;
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    .section h2 {{
      margin: 0 0 8px 0;
      font-size: 15px;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }}
    .repo-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}
    .repo-card {{
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      padding: 10px;
      break-inside: avoid;
      page-break-inside: avoid;
    }}
    .repo-card h3 {{
      margin: 0;
      font-size: 13px;
    }}
    .repo-card p {{
      margin: 7px 0;
      color: #334155;
      font-size: 11px;
    }}
    .repo-top {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }}
    .repo-meta {{
      display: flex;
      gap: 10px;
      color: #475569;
      font-size: 11px;
    }}
    .repo-url {{
      margin-top: 6px;
      font-size: 10px;
      color: #1d4ed8;
      word-break: break-all;
    }}
    .badge {{
      border: 1px solid #fde68a;
      background: #fef9c3;
      color: #92400e;
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 10px;
      white-space: nowrap;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
    }}
    th, td {{
      padding: 7px 8px;
      border-bottom: 1px solid #e2e8f0;
      text-align: left;
      vertical-align: top;
      font-size: 11px;
    }}
    th {{
      color: #475569;
      font-weight: 600;
      background: #f8fafc;
    }}
    .num {{
      text-align: right;
    }}
    .muted {{
      color: #64748b;
    }}
    .footer {{
      color: #94a3b8;
      font-size: 10px;
      text-align: right;
      margin-top: 2px;
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="header">
      {avatar_html}
      <div class="title">
        <h1>{user_name}</h1>
        <div class="sub">DevHistory Portfolio</div>
        <div class="bio">{user_bio or " "}</div>
        <div class="links">
          <span><strong>Email:</strong> {user_email}</span>
          <span><strong>GitHub:</strong> {github_row}</span>
        </div>
      </div>
    </section>

    <section class="stats">
      <div class="stat"><div class="k">Repositories</div><div class="v">{stats.get("total_repos") or 0}</div></div>
      <div class="stat"><div class="k">Total Commits</div><div class="v">{stats.get("total_commits") or 0}</div></div>
      <div class="stat"><div class="k">Solved Problems</div><div class="v">{stats.get("total_problems") or 0}</div></div>
      <div class="stat"><div class="k">Blog Posts</div><div class="v">{stats.get("total_blogs") or 0}</div></div>
    </section>

    <section class="section">
      <h2>Top Projects</h2>
      <div class="repo-grid">{repo_cards}</div>
    </section>

    <section class="grid-2">
      <section class="section">
        <h2>Languages</h2>
        <table>
          <thead><tr><th>Language</th><th class="num">Repos</th></tr></thead>
          <tbody>{language_rows}</tbody>
        </table>
      </section>

      <section class="section">
        <h2>Activity Summary</h2>
        <table>
          <tbody>
            <tr><th>Total Stars</th><td class="num">{stats.get("total_stars") or 0}</td></tr>
            <tr><th>Active Days</th><td class="num">{stats.get("activity_days") or 0}</td></tr>
            <tr><th>Recent 30d Commits</th><td class="num">{stats.get("recent_commits") or 0}</td></tr>
          </tbody>
        </table>
      </section>
    </section>

    <section class="section">
      <h2>Recent Activity</h2>
      <table>
        <thead><tr><th style="width:90px;">Date</th><th style="width:160px;">Repository</th><th>Message</th></tr></thead>
        <tbody>{activity_rows}</tbody>
      </table>
    </section>

    <div class="footer">Generated by DevHistory · {datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")}</div>
  </main>
</body>
</html>"""


@router.get("/portfolio/pdf")
async def export_portfolio_pdf(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate and download portfolio PDF rendered by headless browser."""
    portfolio = await get_portfolio(current_user=current_user, db=db)
    html = _render_portfolio_pdf_html(portfolio)

    try:
        from playwright.async_api import async_playwright
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="PDF renderer is not available. Install Playwright and Chromium browser.",
        )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            page = await browser.new_page(viewport={"width": 1440, "height": 2200})
            await page.emulate_media(media="screen")
            await page.set_content(html, wait_until="networkidle")
            pdf_bytes = await page.pdf(
                format="A4",
                print_background=True,
                prefer_css_page_size=True,
                margin={"top": "12mm", "right": "12mm", "bottom": "12mm", "left": "12mm"},
            )
            await browser.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

    filename = "devhistory-portfolio.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


class ShareSettingsUpdate(BaseModel):
    portfolio_public: Optional[bool] = None
    public_slug: Optional[str] = None
    portfolio_show_email: Optional[bool] = None
    share_token_expires_days: Optional[int] = None  # 0 = no expiry


class ShareSettingsResponse(BaseModel):
    portfolio_public: bool
    public_slug: Optional[str]
    portfolio_show_email: bool
    share_token: Optional[str]
    share_token_expires_at: Optional[str]
    public_url: Optional[str]
    share_url: Optional[str]


def _share_response(profile: UserProfile) -> dict:
    return {
        "portfolio_public": profile.portfolio_public or False,
        "public_slug": profile.public_slug,
        "portfolio_show_email": profile.portfolio_show_email or False,
        "share_token": profile.share_token,
        "share_token_expires_at": profile.share_token_expires_at.isoformat() if profile.share_token_expires_at else None,
        "public_url": f"/u/{profile.public_slug}" if profile.public_slug and profile.portfolio_public else None,
        "share_url": f"/s/{profile.share_token}" if profile.share_token else None,
    }


@router.get("/share-settings", response_model=ShareSettingsResponse)
async def get_share_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return _share_response(profile)


@router.put("/share-settings", response_model=ShareSettingsResponse)
async def update_share_settings(
    data: ShareSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    if data.portfolio_public is not None:
        profile.portfolio_public = data.portfolio_public

    if data.public_slug is not None:
        slug = data.public_slug.strip().lower()
        if len(slug) < 3 or len(slug) > 40:
            raise HTTPException(400, "Slug must be 3-40 characters")
        if not slug.replace("-", "").replace("_", "").isalnum():
            raise HTTPException(400, "Slug may only contain letters, digits, hyphens, underscores")
        existing = db.query(UserProfile).filter(
            UserProfile.public_slug == slug,
            UserProfile.user_id != current_user.id,
        ).first()
        if existing:
            raise HTTPException(409, "This slug is already taken")
        profile.public_slug = slug

    if data.portfolio_show_email is not None:
        profile.portfolio_show_email = data.portfolio_show_email

    if data.share_token_expires_days is not None:
        if data.share_token_expires_days == 0:
            profile.share_token_expires_at = None
        else:
            profile.share_token_expires_at = datetime.utcnow() + timedelta(days=data.share_token_expires_days)

    profile.public_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return _share_response(profile)


@router.post("/share/rotate", response_model=ShareSettingsResponse)
async def rotate_share_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a new private share token (invalidates previous)."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    profile.share_token = secrets.token_urlsafe(32)
    if not profile.share_token_expires_at:
        profile.share_token_expires_at = datetime.utcnow() + timedelta(days=7)
    profile.public_updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return _share_response(profile)


@router.delete("/share")
async def revoke_share(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke share token and disable public portfolio."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(404, "No profile found")

    profile.share_token = None
    profile.share_token_expires_at = None
    profile.portfolio_public = False
    profile.public_updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True}
