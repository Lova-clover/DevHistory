# Oracle Cloud Always Free – DevHistory 프로덕션 배포 가이드

> **대상 환경:** Oracle Cloud Infrastructure (OCI) Always Free  
> **도메인:** devhistory.kr (가비아 구매)  
> **스택:** Docker Compose · Caddy HTTPS · FastAPI · Next.js · Celery · Postgres · Redis

---

## 목차

1. [OCI VM 생성](#1-oci-vm-생성)
2. [서버 초기 설정](#2-서버-초기-설정)
3. [DNS 설정 (가비아)](#3-dns-설정-가비아)
4. [GitHub OAuth App 생성](#4-github-oauth-app-생성)
5. [.env 작성](#5-env-작성)
6. [배포 실행](#6-배포-실행)
7. [배포 후 점검 체크리스트](#7-배포-후-점검-체크리스트)
8. [백업 전략](#8-백업-전략)
9. [업데이트 방법](#9-업데이트-방법)
10. [트러블슈팅](#10-트러블슈팅)
11. [무료 운영 현실 체크](#11-무료-운영-현실-체크)

---

## 1. OCI VM 생성

### 1-1. 인스턴스 유형 선택: Ampere A1 vs AMD x86

| | **Ampere A1 (ARM)** ✅ 추천 | **AMD x86 (E2.1.Micro)** |
|---|---|---|
| Always Free 할당 | **최대 4 OCPU + 24 GB RAM** (계정당) | 2대 × 1/8 OCPU + 1 GB RAM |
| 실제 성능 | **훨씬 우세** | 매우 빡빡함 (1 GB RAM → OOM 위험) |
| Docker 호환성 | ✅ 공식 arm64 이미지 지원 | ✅ amd64 네이티브 |
| DevHistory 빌드 | ✅ `python:3.11-slim`·`node:20-alpine` 멀티아치 지원 | ✅ 동일 |
| 가용성 | 리전에 따라 재고 부족 가능 | 거의 항상 생성 가능 |

**추천: Ampere A1** — 1 OCPU + 6 GB RAM 구성으로 생성하면 여유 있게 운영 가능.  
(4 OCPU + 24 GB는 계정 한도 내에서 최대치이며, 테스트는 1 OCPU + 6 GB도 충분)

> **재고 부족 시:** 콘솔에서 `Out of host capacity` 오류가 나면 다른 Availability Domain(AD)을 선택하거나, 수 분~수 시간 후 재시도. 또는 x86 E2.1.Micro 2대를 조합.

---

### 1-2. VM 생성 절차

1. [OCI 콘솔](https://cloud.oracle.com) 로그인
2. **컴퓨트 → 인스턴스 → 인스턴스 생성** 클릭
3. 설정:
   - **이름:** `devhistory-prod`
   - **이미지:** `Canonical Ubuntu` → **22.04 (또는 24.04)**
   - **Shape:**
     - `Ampere` 탭 → `VM.Standard.A1.Flex`
     - OCPU: `1`, RAM: `6 GB` (최소 추천)
   - **네트워킹:** 기존 VCN 또는 새 VCN 생성 (기본값 OK)
   - **SSH 키:** 로컬 공개키 붙여넣기 또는 새로 생성 후 `.pem` 다운로드
4. **퍼블릭 IP 할당 확인** (기본으로 Ephemeral IP가 할당됨)
   - **⚠️ 중요:** Ephemeral IP는 인스턴스 정지/종료 시 변경될 수 있음 → **Reserved IP로 전환 권장**
5. **생성** 클릭

---

### 1-3. Reserved (고정) Public IP 설정

> 무료 인스턴스를 정지하거나 재생성하면 Ephemeral IP가 바뀌어 가비아 DNS A 레코드를 다시 설정해야 합니다.  
> **Reserved IP는 Always Free 계정에서도 무료**이므로 반드시 설정합니다.

1. OCI 콘솔 → **네트워킹 → IP 관리 → 예약된 공용 IP**
2. **IP 주소 예약** 클릭 (이름: `devhistory-ip`)
3. 생성 후: **컴퓨트 → 인스턴스 → devhistory-prod**
4. 연결된 VNIC 클릭 → **IPv4 주소** → 기존 Ephemeral IP 편집 → **예약된 IP로 할당**

---

### 1-4. Security List / NSG에서 포트 오픈

> OCI는 기본적으로 **22번 외 모든 인바운드 포트가 차단**됩니다.  
> Caddy HTTPS를 사용하려면 **80, 443**을 반드시 열어야 합니다.

**방법 A: VCN Security List (기본)**

1. OCI 콘솔 → **네트워킹 → 가상 클라우드 네트워크** → 해당 VCN 클릭
2. **Security Lists** → `Default Security List` 클릭
3. **인그레스 규칙 추가:**

| 소스 CIDR | IP 프로토콜 | 소스 포트 | 대상 포트 | 설명 |
|-----------|------------|----------|-----------|------|
| `0.0.0.0/0` | TCP | All | `80` | HTTP |
| `0.0.0.0/0` | TCP | All | `443` | HTTPS |

**방법 B: Network Security Group (권장)**

Security List 대신 NSG를 인스턴스에 직접 붙이는 방식. 규칙 동일.

> **추가 주의 (OCI+Ubuntu):** Ubuntu의 iptables가 VCN Security List와 별도로 동작합니다.  
> `server_bootstrap_ubuntu.sh`가 iptables에도 80/443을 허용하므로 스크립트 실행 필수.

---

### 1-5. SSH 접속 확인

```bash
# .pem 키 권한 설정 (macOS/Linux)
chmod 400 ~/Downloads/devhistory-key.pem

# Ampere A1: 기본 유저는 ubuntu
ssh -i ~/Downloads/devhistory-key.pem ubuntu@<OCI_PUBLIC_IP>
```

---

## 2. 서버 초기 설정

```bash
# 서버에 접속 후
git clone https://github.com/YOUR_USER/DevHistory.git ~/devhistory
cd ~/devhistory

# Docker, UFW, iptables 규칙, swap 등 자동 설정
sudo bash scripts/server_bootstrap_ubuntu.sh
```

완료 후 **로그아웃 → 재로그인** (docker 그룹 반영).

---

## 3. DNS 설정 (가비아)

> OCI 인스턴스의 **Reserved Public IP**를 먼저 확인하세요.

### 3-1. 가비아 DNS 설정

1. [gabia.com](https://gabia.com) 로그인 → **서비스 관리 → 도메인 → devhistory.kr**
2. **DNS 설정 → DNS 관리** 클릭
3. 레코드 추가:

| 타입 | 호스트 | 값/IP | TTL |
|------|--------|-------|-----|
| `A` | `@` | `<OCI Public IP>` | 300 |
| `A` | `www` | `<OCI Public IP>` | 300 |

> `@` = 루트 도메인 (`devhistory.kr`)  
> `www` = `www.devhistory.kr` (선택사항)

### 3-2. DNS 전파 확인

```bash
# 로컬 또는 서버에서 실행
nslookup devhistory.kr
# 또는
dig devhistory.kr A +short

# 기대 결과: OCI Public IP 출력
```

> **DNS 전파 시간:** 가비아 TTL 300초 기준 수 분 내 반영. 최대 48시간이지만 대부분 5~10분 내.  
> 전파 전에 Caddy를 시작하면 Let's Encrypt 발급이 실패하므로 **전파 확인 후 배포 진행**.

---

## 4. GitHub OAuth App 생성

1. GitHub → **Settings → Developer settings → OAuth Apps → New OAuth App**
2. 설정:

| 항목 | 값 |
|------|-----|
| Application name | `DevHistory` |
| Homepage URL | `https://devhistory.kr` |
| Authorization callback URL | `https://devhistory.kr/api/auth/github/callback` |

3. **Register application** 클릭
4. **Client ID** 복사
5. **Generate a new client secret** → **Client Secret** 복사
6. `.env` 파일에 반영 (아래 섹션 참조)

> ⚠️ Callback URL이 정확히 일치하지 않으면 OAuth 로그인이 `redirect_uri_mismatch`로 실패합니다.

---

## 5. .env 작성

```bash
cd ~/devhistory
cp infra/.env.prod.example .env
nano .env   # 또는 vim .env
```

| 변수 | 값 | 생성 방법 |
|------|-----|-----------|
| `DOMAIN` | `devhistory.kr` | 직접 입력 |
| `POSTGRES_PASSWORD` | 강력한 패스워드 | `openssl rand -base64 32` |
| `JWT_SECRET` | 랜덤 시크릿 | `python3 -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `CREDENTIALS_ENCRYPTION_KEY` | Fernet 키 | `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `GITHUB_CLIENT_ID` | GitHub OAuth App에서 복사 | 위 4번 참조 |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App에서 복사 | 위 4번 참조 |
| `GITHUB_REDIRECT_URI` | `https://devhistory.kr/api/auth/github/callback` | 직접 입력 |
| `OPENAI_API_KEY` | OpenAI API 키 (선택) | [platform.openai.com](https://platform.openai.com) |
| `ADMIN_GITHUB_USERNAMES` | 본인 GitHub 유저명 | 직접 입력 |

완성된 `.env` 예시:

```dotenv
DOMAIN=devhistory.kr
POSTGRES_DB=devhistory
POSTGRES_USER=devhistory
POSTGRES_PASSWORD=Str0ngP@ssw0rd!2026
JWT_SECRET=<openssl-rand-base64-64-output>
GITHUB_CLIENT_ID=Ov23li...
GITHUB_CLIENT_SECRET=abc123...
GITHUB_REDIRECT_URI=https://devhistory.kr/api/auth/github/callback
OPENAI_API_KEY=sk-...
CREDENTIALS_ENCRYPTION_KEY=<fernet-key>
COOKIE_DOMAIN=devhistory.kr
COOKIE_SECURE=true
ADMIN_GITHUB_USERNAMES=your-github-username
```

---

## 6. 배포 실행

```bash
cd ~/devhistory

# 처음 배포 or 코드 변경 후 재배포 — 단 한 줄
bash scripts/deploy_prod.sh
```

스크립트가 자동으로:
1. `.env` 필수 변수 검증
2. `git pull origin main`
3. `docker compose up -d --build`
4. DB healthy 대기
5. `alembic upgrade head` (마이그레이션)
6. `curl https://devhistory.kr/health` 헬스체크 (최대 120초 재시도)

---

## 7. 배포 후 점검 체크리스트

```bash
# ✅ 1. 모든 컨테이너 Running 상태 확인
docker compose -f infra/docker-compose.prod.yml ps

# ✅ 2. API 헬스체크
curl https://devhistory.kr/health
# 기대값: {"status":"healthy"}

# ✅ 3. HTTPS 인증서 확인
curl -I https://devhistory.kr
# Strict-Transport-Security 헤더가 있으면 OK

# ✅ 4. Caddy 로그 (TLS 발급 확인)
docker compose -f infra/docker-compose.prod.yml logs caddy | grep -E "certificate|tls|error"

# ✅ 5. API 로그
docker compose -f infra/docker-compose.prod.yml logs --tail=30 api

# ✅ 6. Worker & Beat 로그
docker compose -f infra/docker-compose.prod.yml logs --tail=30 worker
docker compose -f infra/docker-compose.prod.yml logs --tail=30 beat

# ✅ 7. 브라우저 확인
# https://devhistory.kr         → 랜딩 페이지
# https://devhistory.kr/login   → GitHub 로그인 버튼
# https://devhistory.kr/docs    → FastAPI Swagger UI
# https://devhistory.kr/admin   → 관리자 대시보드 (ADMIN_GITHUB_USERNAMES 설정 필요)

# ✅ 8. GitHub OAuth 로그인 테스트
# /login → GitHub으로 로그인 → 콜백 성공 → /onboarding 또는 /dashboard 리다이렉트
```

---

## 8. 백업 전략

### 8-1. 수동 백업

```bash
# Postgres 덤프
docker compose -f ~/devhistory/infra/docker-compose.prod.yml exec db \
    pg_dump -U devhistory devhistory > ~/backup_$(date +%Y%m%d_%H%M%S).sql

# 압축
gzip ~/backup_*.sql
```

### 8-2. 자동 백업 (cron)

```bash
# crontab 편집
crontab -e

# 매일 새벽 3시 Postgres 백업, 7일치 보관
0 3 * * * cd ~/devhistory && docker compose -f infra/docker-compose.prod.yml exec -T db pg_dump -U devhistory devhistory | gzip > ~/backups/devhistory_$(date +\%Y\%m\%d).sql.gz && find ~/backups/ -name "*.sql.gz" -mtime +7 -delete
```

백업 디렉토리 미리 생성:

```bash
mkdir -p ~/backups
```

### 8-3. 복원

```bash
gunzip -c ~/backups/devhistory_20260301.sql.gz | \
    docker compose -f infra/docker-compose.prod.yml exec -T db \
    psql -U devhistory devhistory
```

---

## 9. 업데이트 방법

```bash
cd ~/devhistory

# 코드 배포 + 마이그레이션 + 헬스체크 자동화
bash scripts/deploy_prod.sh
```

### 다운타임 최소화 팁

- `docker compose up -d --build`는 서비스를 **하나씩 재시작**합니다.  
  Caddy ↔ web 사이의 순간 단절이 수 초 발생할 수 있습니다.
- 완전 무중단이 필요하다면: 새 컨테이너 빌드 후 한 번에 스위칭하는 Blue-Green이 필요하지만, Always Free 단일 VM에서는 리소스 한계로 어렵습니다.
- **DB 마이그레이션 전략:** 항상 `upgrade head`는 idempotent하게 작성 (Alembic 기본 동작). 롤백 필요 시:

```bash
# 한 버전 롤백
docker compose -f infra/docker-compose.prod.yml exec api \
    alembic -c /app/infra/alembic.ini downgrade -1
```

---

## 10. 트러블슈팅

### 🔴 문제 1: Caddy TLS 인증서 발급 실패

**증상:** `https://devhistory.kr` 접속 불가, Caddy 로그에 `ACME` 오류

**원인 & 해결:**

```bash
# Caddy 로그 확인
docker compose -f infra/docker-compose.prod.yml logs caddy | tail -50

# 체크리스트
# 1. OCI Security List에서 80/443 인바운드 열림 확인
# 2. OCI 인스턴스 Ubuntu iptables에 80/443 허용 확인
sudo iptables -L INPUT -n -v | grep -E "80|443"
# 3. DNS A 레코드가 이 서버 IP를 가리키는지 확인
dig devhistory.kr A +short
# 4. Caddy data 볼륨 초기화 후 재시도
docker compose -f infra/docker-compose.prod.yml down
docker volume rm devhistory_caddy_data
docker compose -f infra/docker-compose.prod.yml up -d
```

> **Let's Encrypt 속도 제한:** 동일 도메인에 1주일에 5회 발급 실패 시 제한됩니다.  
> 테스트 중이라면 Caddyfile 상단에 `{ acme_ca https://acme-staging-v02.api.letsencrypt.org/directory }` 를 추가해 스테이징 CA로 테스트.

---

### 🔴 문제 2: DNS 미반영

**증상:** `nslookup devhistory.kr`이 OCI IP를 반환하지 않음

```bash
# 현재 NS 확인
dig devhistory.kr NS
# 가비아 네임서버(ns1.gabia.net 등)가 나와야 함

# 전파 맞는지 확인
nslookup devhistory.kr 8.8.8.8   # Google DNS 기준
nslookup devhistory.kr 1.1.1.1   # Cloudflare DNS 기준
```

→ 가비아 DNS 관리 콘솔에서 A 레코드가 정확히 입력됐는지 재확인.

---

### 🔴 문제 3: GitHub OAuth 콜백 불일치

**증상:** GitHub 로그인 후 `redirect_uri_mismatch` 오류

**해결:**
1. GitHub → Settings → Developer settings → OAuth Apps → DevHistory
2. **Authorization callback URL** 정확히: `https://devhistory.kr/api/auth/github/callback`
3. `.env`의 `GITHUB_REDIRECT_URI`도 동일한지 확인
4. API 컨테이너 재시작: `docker compose -f infra/docker-compose.prod.yml restart api`

---

### 🔴 문제 4: DB 마이그레이션 실패

**증상:** `deploy_prod.sh` 5단계에서 오류 발생

```bash
# 수동 실행으로 오류 메시지 확인
docker compose -f infra/docker-compose.prod.yml exec api \
    alembic -c /app/infra/alembic.ini current

docker compose -f infra/docker-compose.prod.yml exec api \
    alembic -c /app/infra/alembic.ini upgrade head

# DB 직접 접속
docker compose -f infra/docker-compose.prod.yml exec db \
    psql -U devhistory devhistory
```

---

### 🔴 문제 5: Worker / Beat 미동작

**증상:** Celery 태스크가 실행되지 않음 (GitHub 동기화, 블로그 생성 등 무반응)

```bash
# Worker 로그 확인
docker compose -f infra/docker-compose.prod.yml logs --tail=50 worker

# Redis 연결 확인
docker compose -f infra/docker-compose.prod.yml exec redis redis-cli ping
# 기대값: PONG

# Worker 재시작
docker compose -f infra/docker-compose.prod.yml restart worker beat
```

---

### 🔴 문제 6: OOM (메모리 부족)

**증상:** 컨테이너가 갑자기 죽음 (`OOMKilled`)

```bash
# 메모리 사용 확인
docker stats --no-stream

# Swap 상태 확인 (bootstrap 스크립트로 2GB 설정했다면)
free -h
swapon --show
```

→ Ampere A1을 6 GB 이상으로 생성했다면 거의 발생 안 함. x86 1 GB VM이라면 심각.

---

## 11. 무료 운영 현실 체크

### Always Free 정책 변경 가능성

> Oracle은 Always Free 정책을 변경한 이력이 있습니다 (2022년 기존 계정 리소스 회수 시도).  
> **백업을 주기적으로 로컬 또는 다른 스토리지로 내려받는 것을 강력히 권장합니다.**

- OCI Always Free 리소스는 **계정이 활성 상태**여야 유지됩니다 (최소 90일마다 로그인 권장)
- 특정 리전에서 A1 Shape 재고가 소진되면 **신규 생성 불가** (기존 인스턴스는 유지)
- 리전은 최초 계정 생성 시 고정 (서울 리전 `ap-seoul-1` 권장)

### IP 변경 가능성

| 상황 | IP 변동 여부 |
|------|------------|
| 인스턴스 재부팅 | Ephemeral IP → ❌ 변동 없음 |
| 인스턴스 **정지 후 시작** | Ephemeral IP → ⚠️ **변동 가능** |
| Reserved IP 사용 | ✅ 항상 고정 |

→ **Reserved IP 설정 필수** (무료). 변동됐다면:

```bash
# 가비아 A 레코드 업데이트 후 DNS 전파 확인
dig devhistory.kr A +short
```

### 비용 주의

Always Free 한도를 초과하는 리소스(Block Storage 초과, Outbound 데이터 등)는 과금될 수 있습니다.  
OCI 콘솔 → **거버넌스 → 예산** 에서 월별 예산 알림을 설정하세요.

---

## 요약: 전체 배포 명령어 순서

```bash
# ① 서버에 SSH 접속
ssh -i ~/devhistory-key.pem ubuntu@<OCI_PUBLIC_IP>

# ② 리포 클론
git clone https://github.com/YOUR_USER/DevHistory.git ~/devhistory
cd ~/devhistory

# ③ 서버 초기화 (Docker, UFW, iptables, Swap)
sudo bash scripts/server_bootstrap_ubuntu.sh

# ④ 재로그인 후
cd ~/devhistory

# ⑤ .env 작성
cp infra/.env.prod.example .env && nano .env

# ⑥ 배포
bash scripts/deploy_prod.sh

# ⑦ 확인
curl https://devhistory.kr/health
docker compose -f infra/docker-compose.prod.yml ps
```

**배포 성공 판정 체크리스트:**

- [ ] `docker compose ps` — 6개 컨테이너 모두 `Up` (caddy/db/redis/api/worker/beat/web)
- [ ] `curl https://devhistory.kr/health` → `{"status":"healthy"}`
- [ ] 브라우저 `https://devhistory.kr` → 랜딩 페이지 (HTTPS 자물쇠 표시)
- [ ] `https://devhistory.kr/login` → GitHub 로그인 후 `/dashboard` 이동
- [ ] `https://devhistory.kr/docs` → Swagger UI 정상 렌더링
