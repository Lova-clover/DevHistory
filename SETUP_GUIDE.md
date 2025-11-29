# DevHistory - Production Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

## Quick Start

### 1. Environment Setup

Create `.env` file in the project root:

```bash
# Database
DATABASE_URL=postgresql://devhistory:devhistory123@db:5432/devhistory

# Redis
REDIS_URL=redis://redis:6379/0

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_CALLBACK_URL=http://localhost:8000/auth/github/callback

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### 2. Start Services

```bash
# Build and start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f web
```

### 3. Database Migration

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create initial user (optional)
docker-compose exec api python -c "
from app.database import SessionLocal
from app.models.user import User
db = SessionLocal()
user = User(github_username='your_username', email='your@email.com')
db.add(user)
db.commit()
print(f'Created user: {user.id}')
"
```

### 4. Install Frontend Dependencies

```bash
cd apps/web
npm install
```

### 5. Access the Application

- **Frontend**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Redoc**: http://localhost:8000/redoc

## Development Workflow

### Backend Development

```bash
# Enter API container
docker-compose exec api bash

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Format code
black app/
isort app/

# Type checking
mypy app/
```

### Frontend Development

```bash
cd apps/web

# Development server
npm run dev

# Build for production
npm run build

# Start production server
npm run start

# Linting
npm run lint
```

### Worker Development

```bash
# Check worker status
docker-compose exec worker celery -A worker.celery_app inspect active

# Check scheduled tasks
docker-compose exec beat celery -A worker.celery_app inspect scheduled

# Purge all tasks
docker-compose exec worker celery -A worker.celery_app purge
```

## API Usage Examples

### 1. Authentication

```bash
# GitHub OAuth Login
# Visit: http://localhost:8000/auth/github

# After callback, you'll receive a token
export TOKEN="your_jwt_token_here"
```

### 2. Sync Data

```bash
# Sync GitHub repositories
curl -X POST http://localhost:8000/collector/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source": "github", "force_full_sync": false}'

# Sync solved.ac problems
curl -X POST http://localhost:8000/collector/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source": "solvedac", "force_full_sync": false}'

# Sync Velog blog posts
curl -X POST http://localhost:8000/collector/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source": "velog", "force_full_sync": false}'
```

### 3. Check Sync Status

```bash
curl -X GET http://localhost:8000/collector/status \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Get Dashboard Stats

```bash
curl -X GET http://localhost:8000/dashboard/stats \
  -H "Authorization: Bearer $TOKEN"
```

### 5. Create Weekly Summary

```bash
curl -X POST http://localhost:8000/weekly \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-07",
    "regenerate": false
  }'
```

### 6. Generate Content

```bash
curl -X POST http://localhost:8000/generate/content \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "blog_post",
    "title": "My Weekly Development Journey",
    "context": "Focus on React and TypeScript projects",
    "use_style_profile": true
  }'
```

## Production Deployment

### 1. Security Checklist

- [ ] Change all default passwords and secrets
- [ ] Enable HTTPS (SSL/TLS certificates)
- [ ] Set up firewall rules
- [ ] Enable CORS with specific origins
- [ ] Use environment-specific configurations
- [ ] Enable rate limiting on API endpoints
- [ ] Set up monitoring and alerting

### 2. Environment Variables for Production

```bash
# Use strong, randomly generated secrets
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Use production database
DATABASE_URL=postgresql://user:password@prod-db:5432/devhistory

# Use production Redis
REDIS_URL=redis://prod-redis:6379/0

# Enable HTTPS
HTTPS_ENABLED=true

# Set CORS origins
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Sentry for error tracking (optional)
SENTRY_DSN=your_sentry_dsn

# Log level
LOG_LEVEL=INFO
```

### 3. Docker Compose for Production

```yaml
version: '3.8'

services:
  api:
    build:
      context: .
      dockerfile: infra/api.Dockerfile
    environment:
      - LOG_LEVEL=INFO
      - WORKERS=4
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  worker:
    build:
      context: .
      dockerfile: infra/api.Dockerfile
    command: celery -A worker.celery_app worker --loglevel=info --concurrency=4
    restart: always
    deploy:
      replicas: 2

  web:
    build:
      context: .
      dockerfile: infra/web.Dockerfile
    environment:
      - NODE_ENV=production
    restart: always
```

### 4. Database Backup

```bash
# Backup database
docker-compose exec db pg_dump -U devhistory devhistory > backup_$(date +%Y%m%d).sql

# Restore database
docker-compose exec -T db psql -U devhistory devhistory < backup_20240101.sql
```

### 5. Monitoring Setup

**Health Check Endpoints**:
- API: `GET /health`
- Worker: Check Celery inspect
- Database: Connection pool status

**Metrics to Monitor**:
- API response times
- Error rates
- Database query performance
- Redis memory usage
- Celery task queue length
- Worker processing rate

## Troubleshooting

### Common Issues

#### 1. Database Connection Error

```bash
# Check database is running
docker-compose ps db

# Check logs
docker-compose logs db

# Restart database
docker-compose restart db
```

#### 2. Worker Not Processing Tasks

```bash
# Check worker status
docker-compose logs worker

# Check Celery configuration
docker-compose exec worker celery -A worker.celery_app inspect stats

# Restart worker
docker-compose restart worker
```

#### 3. Frontend Build Errors

```bash
# Clear Next.js cache
cd apps/web
rm -rf .next

# Reinstall dependencies
rm -rf node_modules
npm install

# Rebuild
npm run build
```

#### 4. API Rate Limiting

If you're hitting rate limits:

```python
# Adjust rate limiters in app/utils/retry.py
github_rate_limiter = RateLimiter(rate=120, per=60.0)  # Increase from 60
```

#### 5. Memory Issues

```bash
# Check memory usage
docker stats

# Increase limits in docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 4G  # Increase from 2G
```

## Performance Optimization

### 1. Database Indexing

```sql
-- Add indexes for common queries
CREATE INDEX idx_commit_user_date ON commits(user_id, committed_at DESC);
CREATE INDEX idx_problem_user_date ON problems(user_id, solved_at DESC);
CREATE INDEX idx_blogpost_user_date ON blog_posts(user_id, published_at DESC);
```

### 2. Redis Caching

```python
# Cache expensive queries
@cache_result(ttl=300)  # 5 minutes
async def get_user_stats(user_id: int):
    # Expensive database queries
    pass
```

### 3. Frontend Optimization

```typescript
// Use React.memo for expensive components
export const StatsCard = React.memo(function StatsCard({ ... }) {
  // Component implementation
});

// Use useMemo for expensive calculations
const sortedData = useMemo(() => {
  return data.sort((a, b) => b.date - a.date);
}, [data]);
```

## Contributing

### Code Style

**Backend**:
- Follow PEP 8
- Use type hints
- Write docstrings for all functions
- Keep functions small and focused

**Frontend**:
- Use TypeScript strict mode
- Follow React best practices
- Write JSDoc comments
- Use functional components with hooks

### Testing Requirements

- Minimum 80% code coverage
- All new features must have tests
- Integration tests for API endpoints
- E2E tests for critical user flows

### Pull Request Process

1. Create feature branch from `main`
2. Make changes with descriptive commits
3. Add tests for new functionality
4. Update documentation
5. Submit PR with clear description
6. Address review comments
7. Squash commits before merge

## Support

- **Documentation**: See `/docs` directory
- **API Spec**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Email**: support@devhistory.com

## License

MIT License - See LICENSE file for details
