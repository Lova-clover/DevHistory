# DevHistory Backend Setup Guide

## 환경 설정

### 1. .env 파일 생성
`apps/api/.env` 파일을 생성하고 다음 내용을 추가하세요:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/devhistory

# JWT
JWT_SECRET=your-super-secret-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=30

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/api/auth/github/callback

# Frontend
FRONTEND_URL=http://localhost:3000

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=true
```

### 2. GitHub OAuth App 설정

1. GitHub에서 OAuth App 생성:
   - https://github.com/settings/developers
   - New OAuth App 클릭
   - Application name: DevHistory
   - Homepage URL: http://localhost:3000
   - Authorization callback URL: http://localhost:8000/api/auth/github/callback

2. Client ID와 Client Secret을 .env에 추가

### 3. 데이터베이스 설정

#### PostgreSQL 설치 (선택 1: Docker)
```powershell
docker run --name devhistory-postgres \
  -e POSTGRES_USER=devhistory \
  -e POSTGRES_PASSWORD=devhistory123 \
  -e POSTGRES_DB=devhistory \
  -p 5432:5432 \
  -d postgres:15
```

#### PostgreSQL 설치 (선택 2: 로컬 설치)
- https://www.postgresql.org/download/windows/
- 설치 후 데이터베이스 생성:
```sql
CREATE DATABASE devhistory;
CREATE USER devhistory WITH PASSWORD 'devhistory123';
GRANT ALL PRIVILEGES ON DATABASE devhistory TO devhistory;
```

### 4. Redis 설치

#### Redis (선택 1: Docker)
```powershell
docker run --name devhistory-redis -p 6379:6379 -d redis:7
```

#### Redis (선택 2: WSL)
```bash
# WSL에서 실행
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

### 5. Python 가상환경 설정

```powershell
# 1. 가상환경 생성
cd apps/api
python -m venv venv

# 2. 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 패키지 설치 (editable mode)
pip install -e ../../packages/merge_collector
pip install -e ../../packages/merge_core
pip install -e ../../packages/merge_forge
pip install -e ../../packages/merge_styler
pip install -e ../../packages/merge_timeline
```

### 6. 데이터베이스 마이그레이션

```powershell
# Alembic으로 마이그레이션 실행
cd ../../infra
alembic upgrade head
```

### 7. 서버 실행

#### 터미널 1: API 서버
```powershell
cd apps/api
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 터미널 2: Celery Worker
```powershell
cd apps/api
.\venv\Scripts\Activate.ps1
celery -A worker.celery_app worker --loglevel=info -P solo
```

#### 터미널 3: Celery Beat (스케줄러)
```powershell
cd apps/api
.\venv\Scripts\Activate.ps1
celery -A worker.celery_app beat --loglevel=info
```

#### 터미널 4: Frontend (Node.js 설치 후)
```powershell
cd apps/web
npm install
npm run dev
```

## API 엔드포인트 테스트

### 1. Health Check
```powershell
curl http://localhost:8000/health
```

### 2. API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 3. 인증 테스트
1. 브라우저에서 http://localhost:8000/api/auth/github/login 방문
2. GitHub 로그인
3. Dashboard로 리디렉션

## 주요 구현 완료 사항

### ✅ Backend API
- [x] Dashboard 통계 API (`/api/dashboard/stats`, `/api/dashboard/summary`)
- [x] Weekly 리포트 API (`/api/weekly`)
- [x] Repos API (`/api/repos`)
- [x] 차트 데이터 API (`/api/charts/*`)
  - Commit Activity
  - Language Distribution
  - Activity Heatmap
  - Weekly Comparison

### ✅ Worker Tasks
- [x] GitHub 동기화 (`sync_github_for_user`)
- [x] solved.ac 동기화 (`sync_solvedac_for_user`)
- [x] Velog 동기화 (`sync_velog_for_user`)
- [x] 주간 리포트 생성 (`build_weekly_summary`)

### ✅ 인증 시스템
- [x] GitHub OAuth 로그인
- [x] JWT 토큰 발급/검증
- [x] Protected routes

### ✅ Data Collectors
- [x] GitHub (repos, commits)
- [x] solved.ac (problems)
- [x] Velog (blog posts via RSS)

## 트러블슈팅

### 문제: Port already in use
```powershell
# 포트 사용 중인 프로세스 종료
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### 문제: Database connection failed
- PostgreSQL이 실행 중인지 확인
- .env의 DATABASE_URL이 올바른지 확인
- 방화벽 설정 확인

### 문제: Celery worker 시작 실패
- Redis가 실행 중인지 확인
- Windows에서는 `-P solo` 옵션 필수

### 문제: CORS 에러
- .env의 FRONTEND_URL이 올바른지 확인
- FastAPI CORS middleware 설정 확인

## 다음 단계

1. ✅ Node.js 설치
2. ✅ Frontend 의존성 설치 (`npm install`)
3. ✅ Backend & Frontend 동시 실행
4. ⏳ 실제 데이터로 테스트
5. ⏳ 모바일 반응형 테스트
6. ⏳ 접근성 개선
7. ⏳ Production 배포 준비

## 유용한 명령어

```powershell
# 데이터베이스 초기화
alembic downgrade base
alembic upgrade head

# Celery 작업 모니터링
celery -A worker.celery_app inspect active

# 로그 확인
tail -f logs/api.log

# 테스트 실행
pytest apps/api/tests
```
