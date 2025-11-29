# DevHistory API Specification

Base URL: `http://localhost:8000`

## Authentication

All authenticated endpoints require a JWT token in an httpOnly cookie named `access_token`.

### POST /api/auth/github/login
Redirect to GitHub OAuth authorization page.

**Response**: 302 Redirect to GitHub

### GET /api/auth/github/callback
Handle GitHub OAuth callback and set authentication cookie.

**Query Parameters**:
- `code` (string, required): OAuth authorization code

**Response**: 302 Redirect to `/dashboard` with cookie set

### POST /api/auth/logout
Clear authentication cookie.

**Response**: 
```json
{
  "message": "Logged out successfully"
}
```

## User Information

### GET /api/me
Get current user information.

**Auth**: Required

**Response**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "User Name",
  "avatar_url": "https://..."
}
```

### GET /api/me/connections
Get user's connected accounts status.

**Auth**: Required

**Response**:
```json
{
  "github": true,
  "solvedac": "handle",
  "velog": "@username"
}
```

## Profile Management

### GET /api/profile/user
Get user profile (solved.ac, velog).

**Auth**: Required

**Response**:
```json
{
  "solvedac_handle": "handle",
  "velog_id": "@username"
}
```

### PUT /api/profile/user
Update user profile.

**Auth**: Required

**Request Body**:
```json
{
  "solvedac_handle": "handle",
  "velog_id": "@username"
}
```

**Response**: Same as GET

### GET /api/profile/style
Get user's style profile.

**Auth**: Required

**Response**:
```json
{
  "language": "ko",
  "tone": "technical",
  "blog_structure": ["Intro", "Problem", "Approach", "Result", "Next"],
  "report_structure": ["Summary", "What I did", "Learned", "Next"],
  "extra_instructions": "..."
}
```

### PUT /api/profile/style
Update style profile.

**Auth**: Required

**Request Body**: Same structure as GET response

**Response**: Updated style profile

## Data Collection

### POST /api/collector/trigger/github
Trigger manual GitHub sync.

**Auth**: Required

**Response**:
```json
{
  "message": "GitHub sync triggered",
  "status": "queued"
}
```

### POST /api/collector/trigger/solvedac
Trigger manual solved.ac sync.

**Auth**: Required

**Response**:
```json
{
  "message": "solved.ac sync triggered",
  "status": "queued"
}
```

### POST /api/collector/trigger/velog
Trigger manual Velog sync.

**Auth**: Required

**Response**:
```json
{
  "message": "Velog sync triggered",
  "status": "queued"
}
```

### GET /api/collector/status
Get sync status for all sources.

**Auth**: Required

**Response**:
```json
{
  "github": {
    "status": "idle",
    "last_synced": "2024-01-01T00:00:00Z"
  },
  "solvedac": {
    "status": "running",
    "last_synced": "2024-01-01T00:00:00Z"
  },
  "velog": {
    "status": "idle",
    "last_synced": null
  }
}
```

## Dashboard

### GET /api/dashboard/summary
Get dashboard summary for specified time range.

**Auth**: Required

**Query Parameters**:
- `range` (string): One of `week`, `month`, `year` (default: `week`)

**Response**:
```json
{
  "range": "week",
  "commit_count": 42,
  "problem_count": 15,
  "note_count": 3,
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-08T00:00:00Z"
}
```

## Weekly Reports

### GET /api/weekly
List all weekly summaries for current user.

**Auth**: Required

**Response**:
```json
[
  {
    "id": "uuid",
    "week_start": "2024-01-01",
    "week_end": "2024-01-07",
    "commit_count": 10,
    "problem_count": 5,
    "note_count": 2,
    "has_llm_summary": true
  }
]
```

### GET /api/weekly/{weekly_id}
Get detailed weekly summary.

**Auth**: Required

**Path Parameters**:
- `weekly_id` (uuid, required): Weekly summary ID

**Response**:
```json
{
  "id": "uuid",
  "week_start": "2024-01-01",
  "week_end": "2024-01-07",
  "commit_count": 10,
  "problem_count": 5,
  "note_count": 2,
  "summary_json": {
    "by_day": {
      "2024-01-01": {
        "commits": 2,
        "problems": 1,
        "notes": 0
      }
    },
    "problems_by_tag": {
      "graph": 3,
      "dp": 2
    },
    "commits_by_repo": {
      "user/repo": 5
    }
  },
  "llm_summary": "# 주간 리포트\n\n..."
}
```

## Repositories

### GET /api/repos
List all repositories for current user.

**Auth**: Required

**Response**:
```json
[
  {
    "id": "uuid",
    "full_name": "user/repo",
    "html_url": "https://github.com/user/repo",
    "description": "Repository description",
    "language": "Python",
    "stars": 10,
    "forks": 2,
    "is_fork": false,
    "last_synced_at": "2024-01-01T00:00:00Z"
  }
]
```

### GET /api/repos/{repo_id}
Get detailed repository information.

**Auth**: Required

**Path Parameters**:
- `repo_id` (uuid, required): Repository ID

**Response**:
```json
{
  "id": "uuid",
  "full_name": "user/repo",
  "html_url": "https://github.com/user/repo",
  "description": "Repository description",
  "language": "Python",
  "stars": 10,
  "forks": 2,
  "is_fork": false,
  "last_synced_at": "2024-01-01T00:00:00Z",
  "recent_commits": [
    {
      "sha": "abc123",
      "message": "Commit message",
      "committed_at": "2024-01-01T00:00:00Z",
      "additions": 10,
      "deletions": 5
    }
  ]
}
```

## Content Generation

### POST /api/generate/weekly-report/{weekly_id}
Generate LLM-based weekly report.

**Auth**: Required

**Path Parameters**:
- `weekly_id` (uuid, required): Weekly summary ID

**Response**:
```json
{
  "id": "uuid",
  "content": "# 주간 개발 리포트\n\n...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### POST /api/generate/repo-blog/{repo_id}
Generate blog post draft for a repository.

**Auth**: Required

**Path Parameters**:
- `repo_id` (uuid, required): Repository ID

**Response**:
```json
{
  "id": "uuid",
  "content": "# Project Title\n\n...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

**TODO**: Implement rate limiting
- Unauthenticated: 10 requests/minute
- Authenticated: 100 requests/minute
- LLM generation: 5 requests/hour

## Webhooks

**TODO**: Implement GitHub webhooks for real-time updates
- Push events
- Repository events
- Star events
