# Operations Guide

## Service Architecture

```
Internet → Caddy (80/443) → ┬─ /api/*  → FastAPI (8000)
                             └─ /*      → Next.js (3000)
                             
FastAPI → PostgreSQL (5432)
       → Redis (6379) → Celery Worker
                      → Celery Beat (scheduler)
```

## Common Commands

All commands assume you're in the project root.

```bash
# View running containers
docker compose -f infra/docker-compose.prod.yml ps

# View logs (follow)
docker compose -f infra/docker-compose.prod.yml logs -f api
docker compose -f infra/docker-compose.prod.yml logs -f web
docker compose -f infra/docker-compose.prod.yml logs -f worker

# Restart a specific service
docker compose -f infra/docker-compose.prod.yml restart api
docker compose -f infra/docker-compose.prod.yml restart worker

# Rebuild and restart everything
docker compose -f infra/docker-compose.prod.yml up -d --build

# Run migrations
docker compose -f infra/docker-compose.prod.yml exec api \
  alembic -c /app/infra/alembic.ini upgrade head

# Open a Python shell in the API container
docker compose -f infra/docker-compose.prod.yml exec api python

# Open a psql session
docker compose -f infra/docker-compose.prod.yml exec db \
  psql -U devhistory devhistory
```

## Database Backup & Restore

### Backup

```bash
docker compose -f infra/docker-compose.prod.yml exec db \
  pg_dump -U devhistory devhistory | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
gunzip < backup.sql.gz | docker compose -f infra/docker-compose.prod.yml exec -T db \
  psql -U devhistory devhistory
```

### Automated Backups (cron)

```bash
# Add to crontab:
0 3 * * * cd /path/to/DevHistory && docker compose -f infra/docker-compose.prod.yml exec -T db pg_dump -U devhistory devhistory | gzip > /backups/devhistory_$(date +\%Y\%m\%d).sql.gz
```

## Monitoring

### Health Check

```bash
curl -s https://YOURDOMAIN/health | jq .
# {"status": "healthy"}
```

### Resource Usage

```bash
docker stats --no-stream
```

### Caddy Access Logs

```bash
docker compose -f infra/docker-compose.prod.yml exec caddy \
  cat /data/access.log | tail -50
```

## HTTPS Certificate

Caddy handles certificate provisioning and renewal automatically via Let's Encrypt.
No manual action is needed. Certificates are stored in the `caddy_data` Docker volume.

To force-renew (rarely needed):

```bash
docker compose -f infra/docker-compose.prod.yml restart caddy
```

## Troubleshooting

| Issue | Diagnosis | Fix |
|-------|-----------|-----|
| API 502 | `docker compose logs api` | Check DB connection, restart api |
| Worker not processing | `docker compose logs worker` | Ensure Redis is healthy, restart worker |
| HTTPS cert not issued | Port 80/443 blocked? DNS not pointing? | Check firewall, DNS A record |
| Slow responses | `docker stats` – check memory/CPU | Increase VPS resources or worker count |
| Database full | `docker compose exec db psql -c "SELECT pg_database_size('devhistory');"` | Clean old data or expand disk |

---

## File Cleanup Checklist

> **Status**: `api-client.ts` has been removed. `lib/api.ts` (`fetchWithAuth`) is the single HTTP client.

### Completed

- [x] Identified duplicate HTTP client files (`lib/api.ts` vs `lib/api-client.ts`)
- [x] Verified zero remaining imports of `api-client.ts` across all source files
- [x] Deleted `apps/web/lib/api-client.ts`
- [x] Confirmed all pages and components reference only `@/lib/api` (`fetchWithAuth`)

### Conventions Going Forward

| Rule | Detail |
|------|--------|
| **Single HTTP client** | `apps/web/lib/api.ts` exports `fetchWithAuth`. No other API wrappers. |
| **Analytics helper** | `apps/web/lib/analytics.ts` exports `trackEvent`. All frontend events route through this. |
| **Import style** | Always import as `import { fetchWithAuth } from "@/lib/api"` — never create local fetch wrappers. |
| **New API routes** | Add them in `apps/api/app/routers/` and register in `main.py`. Frontend calls via `fetchWithAuth`. |
| **Duplicate check** | Before creating a new utility under `lib/`, grep the project: `grep -r "from.*lib/" apps/web/` |

### If a Future Duplicate Is Discovered

1. List all imports of the duplicate file: `grep -r "api-client\|apiClient" apps/web/`
2. Replace each import with `fetchWithAuth` from `@/lib/api`
3. Remove the duplicate file
4. Run build to verify: `cd apps/web && npm run build`
5. Verify no 404 API calls in browser DevTools after deploy
