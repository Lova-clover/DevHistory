# Deployment Guide

Deploy DevHistory on a single VPS with HTTPS in ~10 minutes.

## Prerequisites

- A VPS (Ubuntu 22.04+ recommended, 2+ GB RAM)
- A domain name pointing to your VPS IP (A record)
- Docker & Docker Compose v2 installed
- A [GitHub OAuth App](https://github.com/settings/developers)
  - **Authorization callback URL**: `https://YOURDOMAIN/api/auth/github/callback`

## 1. Clone & Configure

```bash
ssh user@your-vps

git clone https://github.com/YOUR_USER/DevHistory.git
cd DevHistory

cp infra/.env.prod.example .env
```

Edit `.env` and fill in all values:

| Variable | How to generate |
|----------|----------------|
| `DOMAIN` | Your domain, e.g. `devhistory.example.com` |
| `POSTGRES_PASSWORD` | `openssl rand -base64 32` |
| `JWT_SECRET` | `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `CREDENTIALS_ENCRYPTION_KEY` | `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `GITHUB_CLIENT_ID` / `SECRET` | From your GitHub OAuth App |
| `GITHUB_REDIRECT_URI` | `https://YOURDOMAIN/api/auth/github/callback` |
| `OPENAI_API_KEY` | Optional (users can bring their own) |
| `ADMIN_GITHUB_USERNAMES` | Your GitHub username |

## 2. Build & Start

```bash
docker compose -f infra/docker-compose.prod.yml up -d --build
```

This starts:
- **Caddy** (ports 80/443) – auto-provisions HTTPS via Let's Encrypt
- **PostgreSQL 15** – data persisted in Docker volume
- **Redis 7** – session/task broker
- **FastAPI** (gunicorn + uvicorn workers)
- **Celery worker + beat** – background tasks
- **Next.js** – production SSR build

## 3. Run Migrations

```bash
docker compose -f infra/docker-compose.prod.yml exec api \
  alembic -c /app/infra/alembic.ini upgrade head
```

## 4. Verify

```bash
# Check all containers are running
docker compose -f infra/docker-compose.prod.yml ps

# Check API health
curl https://YOURDOMAIN/health

# Check logs
docker compose -f infra/docker-compose.prod.yml logs -f api
```

Visit `https://YOURDOMAIN` — you should see the landing page.

## Updating

```bash
cd DevHistory
git pull
docker compose -f infra/docker-compose.prod.yml up -d --build
docker compose -f infra/docker-compose.prod.yml exec api \
  alembic -c /app/infra/alembic.ini upgrade head
```

## Backups

### Database

```bash
docker compose -f infra/docker-compose.prod.yml exec db \
  pg_dump -U devhistory devhistory | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
gunzip < backup_20260201.sql.gz | docker compose -f infra/docker-compose.prod.yml exec -T db \
  psql -U devhistory devhistory
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| 502 Bad Gateway | Check `docker compose logs api` — API may still be starting |
| HTTPS not working | Ensure DNS A record points to VPS, ports 80/443 open |
| OAuth callback fails | Verify GitHub OAuth callback URL matches `https://DOMAIN/api/auth/github/callback` |
| Celery tasks stuck | `docker compose restart worker beat` |
