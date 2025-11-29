from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "devhistory",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "worker.tasks.sync_github",
        "worker.tasks.sync_solvedac",
        "worker.tasks.sync_velog",
        "worker.tasks.build_weekly",
        "worker.tasks.forge_llm",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Celery Beat schedule
celery_app.conf.beat_schedule = {
    "sync-github-every-3-hours": {
        "task": "worker.tasks.sync_github.sync_all_users_github",
        "schedule": crontab(minute=0, hour="*/3"),  # Every 3 hours
    },
    "sync-solvedac-daily": {
        "task": "worker.tasks.sync_solvedac.sync_all_users_solvedac",
        "schedule": crontab(minute=0, hour=3),  # 3 AM daily
    },
    "sync-velog-daily": {
        "task": "worker.tasks.sync_velog.sync_all_users_velog",
        "schedule": crontab(minute=30, hour=3),  # 3:30 AM daily
    },
    "build-weekly-summaries": {
        "task": "worker.tasks.build_weekly.build_all_weekly_summaries",
        "schedule": crontab(minute=0, hour=4, day_of_week=1),  # Monday 4 AM
    },
}
