# DevHistory Architecture

## System Overview

DevHistory is a web service that automatically collects development activities from GitHub, solved.ac, and notes, then generates portfolio and blog content using AI.

## High-Level Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI    │────▶│ PostgreSQL  │
│  Frontend   │     │   Backend    │     │  Database   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │
                           ├──────────────┐
                           │              │
                    ┌──────▼────┐   ┌─────▼──────┐
                    │   Redis   │   │  Celery    │
                    │   Cache   │   │  Workers   │
                    └───────────┘   └────────────┘
                                          │
                                    ┌─────▼──────┐
                                    │  External  │
                                    │  Services  │
                                    │ (GitHub,   │
                                    │ solved.ac, │
                                    │ OpenAI)    │
                                    └────────────┘
```

## Core Modules

### 1. MergeCollector
**Purpose**: Automatic data collection from external sources

**Components**:
- `github.py`: GitHub API integration for repos and commits
- `solvedac.py`: solved.ac API integration for problem solving data
- `velog.py`: Velog RSS feed parsing

**Trigger Methods**:
- Scheduled (Celery Beat): Every 3 hours for GitHub, daily for others
- Manual: User-triggered sync via API endpoints

### 2. MergeTimeline
**Purpose**: Activity aggregation and timeline generation

**Components**:
- `aggregator.py`: Aggregates raw data into summary statistics
- `builder.py`: Builds weekly summaries

**Data Flow**:
1. Query commits, problems, notes for date range
2. Aggregate by day, tag, repository
3. Store in `weekly_summaries` table

### 3. MergeStyler
**Purpose**: User-specific style management

**Components**:
- `prompt_builder.py`: Generates LLM system prompts based on user preferences

**Customization Options**:
- Language (Korean/English)
- Tone (Technical/Casual/Study-note)
- Section structure for blogs and reports
- Extra instructions for LLM

### 4. MergeForge
**Purpose**: AI-powered content generation

**Components**:
- `weekly_report.py`: Generates weekly development reports
- `repo_blog.py`: Generates blog posts for repositories

**LLM Integration**:
- Uses OpenAI API (gpt-4o-mini by default)
- Combines user style with activity data
- Generates markdown-formatted content

### 5. MergeCore
**Purpose**: Shared utilities and configurations

**Components**:
- `llm.py`: OpenAI API wrapper
- `config.py`: Common configuration utilities

## Database Schema

See the detailed schema in the main specification document. Key tables:

- `users`: User accounts
- `oauth_accounts`: OAuth connection info
- `repos`, `commits`: GitHub data
- `problems`: solved.ac data
- `blog_posts`: Velog data
- `notes`: User notes
- `weekly_summaries`: Aggregated weekly data
- `generated_contents`: LLM-generated content
- `style_profiles`: User style preferences
- `user_profiles`: External service handles

## API Structure

### Authentication Flow

1. User clicks "GitHub Login"
2. Redirects to GitHub OAuth
3. GitHub callback to `/api/auth/github/callback`
4. Backend exchanges code for token
5. Creates/updates user and oauth_account
6. Sets JWT cookie
7. Redirects to dashboard

### Main API Routes

- `/api/auth/*`: Authentication endpoints
- `/api/me`: Current user information
- `/api/profile/*`: User and style profile management
- `/api/collector/*`: Data collection triggers
- `/api/dashboard/*`: Dashboard summary data
- `/api/weekly/*`: Weekly reports
- `/api/repos/*`: Repository information
- `/api/generate/*`: LLM content generation

## Background Job System

**Celery Beat Schedule**:
- Every 3 hours: Sync GitHub for all users
- Daily at 3 AM: Sync solved.ac
- Daily at 3:30 AM: Sync Velog
- Monday at 4 AM: Build weekly summaries

**Task Queue (Redis)**:
- User-triggered sync requests
- LLM generation jobs
- Weekly summary builds

## Frontend Architecture

**Next.js App Router Structure**:
```
app/
├── layout.tsx          # Root layout with navigation
├── page.tsx            # Landing page
├── login/              # Login page
├── onboarding/         # Onboarding flow
├── dashboard/          # Main dashboard
├── weekly/             # Weekly reports list
│   └── [id]/           # Weekly report detail
├── repos/              # Repository list
│   └── [id]/           # Repository detail
└── portfolio/          # Portfolio view
```

**State Management**: React hooks (useState, useEffect)
**Styling**: Tailwind CSS
**API Communication**: Fetch API with cookie-based auth

## Deployment

**Docker Compose Services**:
- `db`: PostgreSQL database
- `redis`: Redis cache and queue
- `api`: FastAPI backend
- `worker`: Celery worker
- `beat`: Celery beat scheduler
- `web`: Next.js frontend

**Environment Variables**:
- Database credentials
- GitHub OAuth credentials
- OpenAI API key
- JWT secret
- Frontend URL

## Security Considerations

1. **Authentication**: JWT tokens in httpOnly cookies
2. **Authorization**: User-scoped queries in all endpoints
3. **OAuth**: Secure token storage in database
4. **Environment**: Sensitive data in environment variables
5. **API Rate Limiting**: TODO - implement rate limiting

## Scalability

**Current Design**: Monolithic with microservice-ready architecture
**Future Improvements**:
- Separate collector into standalone service
- Add caching layer (Redis)
- Implement message queue for async processing
- Add horizontal scaling for workers

## Monitoring & Logging

**TODO - To be implemented**:
- Application logging (structured JSON logs)
- Error tracking (Sentry)
- Performance monitoring
- Celery task monitoring

## Development Workflow

1. Create feature branch
2. Implement changes in appropriate module
3. Add tests (if applicable)
4. Update documentation
5. Create pull request
6. Code review
7. Merge to main
8. Deploy via Docker

## Testing Strategy

**Unit Tests**: Individual functions in packages
**Integration Tests**: API endpoints with test database
**E2E Tests**: Critical user flows

## Future Roadmap

1. **Phase 1 (MVP)**: Core features implemented ✅
2. **Phase 2**: Add Notion integration
3. **Phase 3**: Public portfolio pages
4. **Phase 4**: Team features
5. **Phase 5**: Analytics dashboard
