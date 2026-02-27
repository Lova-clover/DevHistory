from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, me, profile, collector, dashboard, weekly, repos, generate, charts
from app.routers import public
from app.routers import llm as llm_router
from app.routers import analytics as analytics_router
from app.routers import coach as coach_router
from app.routers import resume as resume_router

app = FastAPI(
    title="AutoMerge API",
    description="Automatically collect and merge GitHub/solved.ac/notes into portfolio content",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(me.router, prefix="/api/me", tags=["me"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(collector.router, prefix="/api/collector", tags=["collector"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(weekly.router, prefix="/api/weekly", tags=["weekly"])
app.include_router(repos.router, prefix="/api/repos", tags=["repos"])
app.include_router(generate.router, prefix="/api/generate", tags=["generate"])
app.include_router(charts.router, prefix="/api/charts", tags=["charts"])
app.include_router(public.router, prefix="/api/public", tags=["public"])
app.include_router(llm_router.router, prefix="/api/me/llm", tags=["llm"])
app.include_router(analytics_router.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(coach_router.router, prefix="/api/coach", tags=["coach"])
app.include_router(resume_router.router, prefix="/api/resume", tags=["resume"])


@app.get("/")
async def root():
    return {"message": "DevHistory API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
