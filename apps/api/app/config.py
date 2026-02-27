from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/devhistory"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET: str = "dev-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 30
    
    # Cookie settings
    COOKIE_DOMAIN: str = ""
    COOKIE_SECURE: bool = False  # True in production (HTTPS)
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/api/auth/github/callback"
    
    # OpenAI (fallback – users should bring their own key)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # Credentials encryption (Fernet key for BYO LLM keys)
    CREDENTIALS_ENCRYPTION_KEY: str = ""
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Admin
    ADMIN_GITHUB_USERNAMES: str = ""  # comma-separated
    
    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
