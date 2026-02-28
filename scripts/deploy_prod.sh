#!/usr/bin/env bash
# =============================================================
# DevHistory – 프로덕션 배포 스크립트
# =============================================================
# 실행 방법 (레포 루트에서):
#   bash scripts/deploy_prod.sh              # main 브랜치
#   bash scripts/deploy_prod.sh feature/xyz  # 특정 브랜치
#   DOMAIN=devhistory.kr bash scripts/deploy_prod.sh
# =============================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
step()    { echo -e "${CYAN}[STEP]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

COMPOSE_FILE="infra/docker-compose.prod.yml"
ENV_FILE=".env"
BRANCH="${1:-main}"

# ── 0. 레포 루트 확인 ──────────────────────────────────────────
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
info "작업 디렉토리: $REPO_ROOT"

# ── 1. .env 파일 확인 ──────────────────────────────────────────
step "1/6 .env 파일 확인..."
if [[ ! -f "$ENV_FILE" ]]; then
    error ".env 파일이 없습니다. 'cp infra/.env.prod.example .env' 후 값을 입력하세요."
fi

# .env에서 DOMAIN 읽기 (인자로 오버라이드 가능)
if [[ -z "${DOMAIN:-}" ]]; then
    DOMAIN=$(grep -E '^DOMAIN=' "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'")
fi
[[ -z "$DOMAIN" ]] && error ".env에 DOMAIN이 설정되지 않았습니다."
info "배포 대상 도메인: ${DOMAIN}"

# 필수 변수 체크
for VAR in POSTGRES_PASSWORD JWT_SECRET GITHUB_CLIENT_ID GITHUB_CLIENT_SECRET CREDENTIALS_ENCRYPTION_KEY; do
    VAL=$(grep -E "^${VAR}=" "$ENV_FILE" | cut -d'=' -f2- | tr -d '"' | tr -d "'" || true)
    if [[ -z "$VAL" || "$VAL" == CHANGE_ME* ]]; then
        error ".env의 ${VAR}가 설정되지 않았거나 기본값입니다. 실제 값으로 교체하세요."
    fi
done
success ".env 검증 통과"

# ── 2. git pull ───────────────────────────────────────────────
step "2/6 코드 최신화 (브랜치: ${BRANCH})..."
git fetch origin
git checkout "$BRANCH"
git pull origin "$BRANCH"
success "코드 최신화 완료 ($(git rev-parse --short HEAD))"

# ── 3. docker compose build & up ─────────────────────────────
step "3/6 컨테이너 빌드 & 시작..."
docker compose -f "$COMPOSE_FILE" up -d --build --remove-orphans
success "컨테이너 시작 완료"

# ── 4. DB 컨테이너 Healthy 대기 ───────────────────────────────
step "4/6 DB 준비 대기 (최대 60초)..."
for i in $(seq 1 30); do
    STATUS=$(docker compose -f "$COMPOSE_FILE" ps db --format json 2>/dev/null \
             | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Health',''))" 2>/dev/null || echo "")
    if [[ "$STATUS" == "healthy" ]]; then
        success "DB healthy"
        break
    fi
    if [[ $i -eq 30 ]]; then
        warn "DB healthy 상태 미확인. 마이그레이션을 계속 진행합니다 (이미 실행 중일 수 있음)."
    fi
    sleep 2
done

# ── 5. Alembic 마이그레이션 ────────────────────────────────────
step "5/6 DB 마이그레이션 실행..."
docker compose -f "$COMPOSE_FILE" exec -T api \
    alembic -c /app/infra/alembic.ini upgrade head
success "마이그레이션 완료"

# ── 6. 헬스체크 ───────────────────────────────────────────────
step "6/6 헬스체크 (https://${DOMAIN}/health)..."

MAX_RETRIES=12
RETRY_INTERVAL=10
for i in $(seq 1 $MAX_RETRIES); do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
                --max-time 10 \
                "https://${DOMAIN}/health" 2>/dev/null || echo "000")

    if [[ "$HTTP_CODE" == "200" ]]; then
        success "헬스체크 통과 (HTTP 200)"
        break
    fi

    warn "헬스체크 실패 (HTTP ${HTTP_CODE}) — ${i}/${MAX_RETRIES} 시도 중... (${RETRY_INTERVAL}초 대기)"

    if [[ $i -eq $MAX_RETRIES ]]; then
        echo ""
        echo -e "${RED}────────────────────────────────────────────────────${NC}"
        echo -e "${RED}  헬스체크 실패. 트러블슈팅 가이드:${NC}"
        echo -e "${RED}────────────────────────────────────────────────────${NC}"
        echo ""
        echo "  [Caddy 로그 확인]"
        echo "  docker compose -f ${COMPOSE_FILE} logs --tail=50 caddy"
        echo ""
        echo "  [API 로그 확인]"
        echo "  docker compose -f ${COMPOSE_FILE} logs --tail=50 api"
        echo ""
        echo "  [컨테이너 상태 확인]"
        echo "  docker compose -f ${COMPOSE_FILE} ps"
        echo ""
        echo "  [주요 원인]"
        echo "  - OCI Security List / NSG에서 443 포트가 닫혀 있음"
        echo "  - DNS A 레코드가 이 서버 IP를 가리키지 않음"
        echo "  - Caddy Let's Encrypt 발급 실패 (도메인 미반영)"
        echo "  - .env DOMAIN 값이 실제 도메인과 다름"
        echo ""
        echo "  docs/ORACLE_FREE_DEPLOY.md > 트러블슈팅 섹션을 참고하세요."
        exit 1
    fi

    sleep $RETRY_INTERVAL
done

# ── 배포 성공 ─────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║        🚀 DevHistory 배포 성공!             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  서비스 URL:     ${CYAN}https://${DOMAIN}${NC}"
echo -e "  API 헬스체크:   ${CYAN}https://${DOMAIN}/health${NC}"
echo -e "  API 문서:       ${CYAN}https://${DOMAIN}/docs${NC}"
echo -e "  관리자 대시보드: ${CYAN}https://${DOMAIN}/admin${NC}"
echo ""
echo -e "${YELLOW}▶ 배포 후 확인 사항:${NC}"
echo "  1) GitHub OAuth 콜백 URL 확인:"
echo "     https://github.com/settings/developers → DevHistory App"
echo "     Authorization callback URL = https://${DOMAIN}/api/auth/github/callback"
echo ""
echo "  2) 컨테이너 상태 확인:"
echo "     docker compose -f ${COMPOSE_FILE} ps"
echo ""
echo "  3) 로그 실시간 확인:"
echo "     docker compose -f ${COMPOSE_FILE} logs -f api worker"
echo ""
echo "  4) 브라우저에서 https://${DOMAIN} 접속 후 GitHub 로그인 테스트"
echo ""
