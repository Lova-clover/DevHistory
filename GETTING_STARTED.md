# DevHistory 시작 가이드

## 🎯 프로젝트 개요

DevHistory는 개발자의 GitHub 활동, solved.ac 문제 풀이, 블로그/노트를 자동으로 수집하고 AI를 활용해 포트폴리오와 블로그 콘텐츠를 생성하는 웹 서비스입니다.

## 📋 전체 구조

```
devhistory/
├── apps/
│   ├── api/              FastAPI 백엔드 (Python)
│   └── web/              Next.js 프론트엔드 (TypeScript)
├── packages/             공통 Python 패키지들
│   ├── merge_core/       LLM, 설정 등 핵심 유틸
│   ├── merge_collector/  GitHub, solved.ac, Velog 수집
│   ├── merge_timeline/   주간 집계 및 타임라인
│   ├── merge_forge/      LLM 콘텐츠 생성
│   └── merge_styler/     스타일 프로필 관리
├── infra/                Docker 및 DB 마이그레이션
└── docs/                 문서
```

## 🚀 빠른 시작 (Docker)

### 1단계: 환경 변수 설정

```powershell
# .env.example을 .env로 복사
Copy-Item .env.example .env

# .env 파일을 편집하여 필요한 값 설정
# - GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET (GitHub OAuth)
# - OPENAI_API_KEY (OpenAI API)
# - JWT_SECRET (랜덤 문자열로 변경)
```

### 2단계: Docker로 실행

```powershell
cd infra
docker-compose up -d
```

서비스 접속:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3단계: GitHub OAuth 앱 생성

1. GitHub Settings → Developer settings → OAuth Apps
2. **New OAuth App** 클릭
3. 다음 정보 입력:
   - Application name: `DevHistory (Dev)`
   - Homepage URL: `http://localhost:3000`
   - Authorization callback URL: `http://localhost:8000/api/auth/github/callback`
4. Client ID와 Client Secret을 `.env`에 복사

### 4단계: 데이터베이스 초기화

```powershell
# API 컨테이너에서 마이그레이션 실행
docker exec -it devhistory_api alembic upgrade head
```

### 5단계: 사용 시작

1. http://localhost:3000 접속
2. **"GitHub로 시작하기"** 클릭 → GitHub OAuth 인증
3. **온보딩 페이지**에서 연동할 계정 입력:
   - **solved.ac 핸들** (예: `johndoe`) - 선택 사항
   - **Velog ID** (예: `@johndoe`) - 선택 사항
   - **언어, 톤, 섹션 구조** 설정
4. 대시보드로 이동!

**자동 수집 시작:**
- GitHub 데이터는 OAuth 토큰으로 자동 수집
- solved.ac/Velog는 입력한 핸들/ID로 수집
- Celery가 백그라운드에서 주기적으로 동기화

## 💻 로컬 개발 환경 (Docker 없이)

### 사전 요구사항

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+

### 백엔드 설정

```powershell
# 1. 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\activate

# 2. 패키지 설치
pip install -e .

# 3. 환경 변수 설정
Copy-Item .env.example .env
# .env 파일 수정

# 4. PostgreSQL 데이터베이스 생성
# psql -U postgres
# CREATE DATABASE devhistory;

# 5. 마이그레이션 실행
cd infra
$env:PYTHONPATH="$pwd\..\apps\api;$pwd\..\packages"
alembic upgrade head

# 6. API 서버 실행
cd ..\apps\api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Celery Worker 실행 (별도 터미널)

```powershell
.\venv\Scripts\activate
cd apps\api
celery -A worker.celery_app worker --loglevel=info -P solo
```

### Celery Beat 실행 (별도 터미널)

```powershell
.\venv\Scripts\activate
cd apps\api
celery -A worker.celery_app beat --loglevel=info
```

### 프론트엔드 설정

```powershell
# 1. 의존성 설치
cd apps\web
npm install

# 2. 개발 서버 실행
npm run dev
```

프론트엔드 접속: http://localhost:3000

## 🔧 주요 개발 작업

### 새로운 API 엔드포인트 추가

1. `apps/api/app/routers/`에 라우터 파일 생성
2. `apps/api/app/main.py`에서 라우터 등록
3. 필요시 `apps/api/app/models/`에 모델 추가
4. Alembic 마이그레이션 생성: `alembic revision -m "description"`

### 새로운 Celery Task 추가

1. `apps/api/worker/tasks/`에 태스크 파일 생성
2. `apps/api/worker/celery_app.py`의 include에 추가
3. 스케줄 필요시 `beat_schedule`에 추가

### 프론트엔드 페이지 추가

1. `apps/web/app/`에 폴더 및 `page.tsx` 생성
2. Next.js App Router 규칙 따르기
3. API 호출은 `/api/*` 경로 사용 (프록시 설정됨)

## 📦 패키지 구조 설명

### merge_core
- `llm.py`: OpenAI API 래퍼
- `config.py`: 공통 설정

### merge_collector
- `github.py`: GitHub API로 레포, 커밋 수집
- `solvedac.py`: solved.ac API로 문제 풀이 수집
- `velog.py`: Velog RSS로 블로그 포스트 수집

### merge_timeline
- `aggregator.py`: 주간 데이터 집계
- `builder.py`: WeeklySummary 생성

### merge_forge
- `weekly_report.py`: 주간 리포트 LLM 생성
- `repo_blog.py`: 레포지토리 블로그 LLM 생성

### merge_styler
- `prompt_builder.py`: 사용자 스타일 기반 시스템 프롬프트 생성

## 🐛 문제 해결

### Docker 컨테이너가 시작되지 않음
```powershell
docker-compose down
docker-compose up --build
```

### 데이터베이스 연결 오류
- PostgreSQL이 실행 중인지 확인
- `.env`의 `DATABASE_URL` 확인

### Celery worker가 작동하지 않음
- Redis가 실행 중인지 확인
- `REDIS_URL` 환경 변수 확인

### 프론트엔드 빌드 오류
```powershell
cd apps\web
Remove-Item -Recurse -Force node_modules
Remove-Item -Recurse -Force .next
npm install
```

## ✅ 이미 작동하는 기능

현재 프로젝트는 **구조와 플로우가 100% 완성**되어 있습니다:

### 계정 연동 플로우 (완전히 구현됨)
1. ✅ **GitHub OAuth 로그인** - 완벽하게 작동
2. ✅ **온보딩 페이지** - solved.ac 핸들, Velog ID, 스타일 설정
3. ✅ **프로필 저장** - `user_profiles`, `style_profiles` 테이블에 저장
4. ✅ **Celery 스케줄러** - 주기적으로 수집 작업 예약
   - 3시간마다: GitHub 동기화
   - 매일 새벽 3시: solved.ac, Velog 동기화
   - 매주 월요일 4시: 주간 리포트 생성

### 사용자 경험
```
1. http://localhost:3000 접속
2. "GitHub로 시작하기" 클릭 → GitHub OAuth 인증
3. 온보딩 페이지에서 입력:
   - solved.ac 핸들 (예: "johndoe")
   - Velog ID (예: "@johndoe")
   - 언어, 톤, 섹션 구조
4. 대시보드로 이동
5. Celery가 자동으로 데이터 수집 시작!
```

## ⚠️ 추가 구현 필요한 부분

**구조는 완성, 실제 API 호출 로직만 TODO 상태:**

### 1. GitHub 데이터 수집 (우선순위 높음)
**위치:** `packages/merge_collector/github.py`

```python
async def sync_repos(github_token: str, db):
    # TODO: GitHub API로 레포지토리 목록 가져오기
    # GET https://api.github.com/user/repos
    # → Repo 모델에 저장
    pass
```

**필요한 것:**
- GitHub REST API v3 호출
- 페이지네이션 처리
- DB upsert (있으면 업데이트, 없으면 생성)

### 2. solved.ac 데이터 수집
**위치:** `packages/merge_collector/solvedac.py`

```python
async def sync_problems(handle: str, db):
    # TODO: solved.ac API 호출
    # GET https://solved.ac/api/v3/user/problem_stats?handle={handle}
    # → Problem 모델에 저장
    pass
```

### 3. Velog RSS 파싱
**위치:** `packages/merge_collector/velog.py`

```python
async def sync_blog_posts(velog_id: str, db):
    # TODO: RSS 피드 파싱
    # feedparser.parse(f"https://v2.velog.io/rss/@{velog_id}")
    # → BlogPost 모델에 저장
    pass
```

### 4. 주간 집계 강화
**위치:** `packages/merge_timeline/aggregator.py`

현재는 단순 카운트만. 추가 필요:
- 날짜별 활동량 (JSON)
- 문제 유형별 분포
- 레포별 기여도 상위 3개

### 5. LLM 프롬프트 튜닝
**위치:** `packages/merge_forge/*.py`

더 구체적이고 품질 높은 프롬프트 작성

## 📚 다음 단계

### Phase 1: 핵심 데이터 수집 (필수)
1. **GitHub 레포/커밋 수집** - 가장 중요! 이것만 구현해도 기본 동작
2. solved.ac 문제 수집 - 선택적
3. Velog 블로그 수집 - 선택적

### Phase 2: 데이터 활용
4. 주간 집계 로직 강화
5. LLM 프롬프트 튜닝
6. 차트 라이브러리 통합 (Chart.js/Recharts)

### Phase 3: 추가 기능
7. Notion 연동
8. 공개 포트폴리오 페이지
9. 이력서 생성 기능

### Phase 4: 배포 준비
10. 환경별 설정 분리
11. CI/CD 파이프라인
12. 모니터링 설정

## 🤝 기여하기

1. 이슈 생성 또는 기존 이슈 확인
2. Feature 브랜치 생성
3. 변경사항 커밋
4. Pull Request 생성

## 📖 추가 문서

- [아키텍처 문서](docs/ARCHITECTURE.md)
- [API 명세](docs/API_SPEC.md)
- [README](README.md)

## ⚙️ 유용한 명령어

```powershell
# Docker 로그 확인
docker-compose logs -f api
docker-compose logs -f worker

# 데이터베이스 초기화
docker-compose down -v
docker-compose up -d db
docker exec -it devhistory_api alembic upgrade head

# Python 의존성 추가
pip install <package>
pip freeze > requirements.txt

# 마이그레이션 생성
cd infra
alembic revision -m "description"

# 프론트엔드 빌드
cd apps\web
npm run build
```

---

**Happy Coding! 🎉**
