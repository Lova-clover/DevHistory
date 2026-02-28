#!/usr/bin/env bash
# =============================================================
# DevHistory – Ubuntu 22.04 서버 최초 셋업 스크립트
# Oracle Cloud (Ampere A1 / x86) 모두 지원
# =============================================================
# 실행 방법:
#   chmod +x scripts/server_bootstrap_ubuntu.sh
#   sudo bash scripts/server_bootstrap_ubuntu.sh
# =============================================================
set -euo pipefail

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── 0. root 확인 ──────────────────────────────────────────────
[[ $EUID -ne 0 ]] && error "root 또는 sudo로 실행하세요."

ARCH=$(uname -m)
info "감지된 아키텍처: ${ARCH}"

# ── 1. 시스템 업데이트 ─────────────────────────────────────────
info "패키지 업데이트 중..."
apt-get update -qq
apt-get upgrade -y -qq

# ── 2. 기본 패키지 설치 ────────────────────────────────────────
info "기본 패키지 설치 중..."
apt-get install -y -qq \
    git \
    curl \
    wget \
    ca-certificates \
    gnupg \
    lsb-release \
    unzip \
    htop \
    ufw \
    fail2ban

# ── 3. Docker 설치 (공식 저장소) ───────────────────────────────
if command -v docker &>/dev/null; then
    info "Docker 이미 설치됨: $(docker --version)"
else
    info "Docker 설치 중..."
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" \
        > /etc/apt/sources.list.d/docker.list

    apt-get update -qq
    apt-get install -y -qq \
        docker-ce \
        docker-ce-cli \
        containerd.io \
        docker-buildx-plugin \
        docker-compose-plugin

    systemctl enable docker
    systemctl start docker
    info "Docker 설치 완료: $(docker --version)"
fi

# ── 4. 현재 사용자를 docker 그룹에 추가 ───────────────────────
# sudo 없이 docker 명령 실행 가능하게 함
REAL_USER="${SUDO_USER:-ubuntu}"
if id "$REAL_USER" &>/dev/null; then
    usermod -aG docker "$REAL_USER"
    info "${REAL_USER} 사용자를 docker 그룹에 추가했습니다."
    info "반영하려면 로그아웃 후 다시 로그인하세요 (또는 'newgrp docker')."
fi

# ── 5. Docker Compose v2 확인 ─────────────────────────────────
if docker compose version &>/dev/null; then
    info "Docker Compose v2: $(docker compose version)"
else
    error "Docker Compose v2 설치 실패. docker-compose-plugin을 확인하세요."
fi

# ── 6. UFW 방화벽 설정 ─────────────────────────────────────────
info "UFW 방화벽 설정 중..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp   comment 'SSH'
ufw allow 80/tcp   comment 'HTTP (Caddy → HTTPS redirect)'
ufw allow 443/tcp  comment 'HTTPS'
ufw --force enable
info "UFW 방화벽 활성화 완료."
ufw status verbose

# ── 7. OCI iptables 규칙 추가 (Oracle Cloud 필수) ─────────────
# OCI 기본 iptables가 UFW보다 먼저 DROP하는 문제 해결
info "OCI iptables 규칙 추가 중 (80/443 INPUT ACCEPT)..."
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT 2>/dev/null || true
iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT 2>/dev/null || true

# iptables 규칙 영구 저장 (재부팅 시에도 유지)
apt-get install -y -qq iptables-persistent
netfilter-persistent save
info "OCI iptables 규칙 저장 완료."

# ── 8. fail2ban 활성화 (SSH 보호) ─────────────────────────────
systemctl enable fail2ban
systemctl start fail2ban
info "fail2ban 활성화 완료."

# ── 9. swap 설정 (Ampere 1GB 제한 대응) ───────────────────────
# Always Free VM의 RAM이 부족할 때 OOM killer 방지
if swapon --show | grep -q swap; then
    info "Swap 이미 설정됨."
else
    info "2GB Swap 파일 생성 중..."
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    info "Swap 2GB 설정 완료."
fi

# ── 10. 완료 메시지 ────────────────────────────────────────────
echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}  서버 초기 설정 완료!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "${YELLOW}▶ 필수 다음 단계:${NC}"
echo ""
echo "  1) 로그아웃 후 재로그인 (docker 그룹 반영)"
echo ""
echo "  2) 리포지토리 클론:"
echo "     git clone https://github.com/YOUR_USER/DevHistory.git ~/devhistory"
echo "     cd ~/devhistory"
echo ""
echo "  3) .env 파일 생성:"
echo "     cp infra/.env.prod.example .env"
echo "     nano .env   # 모든 값 입력"
echo ""
echo "  4) 배포 실행:"
echo "     chmod +x scripts/deploy_prod.sh"
echo "     bash scripts/deploy_prod.sh"
echo ""
echo "  [참고] OCI 콘솔에서 Security List / NSG에 80/443 인바운드를 반드시 열어야 합니다."
echo "  docs/ORACLE_FREE_DEPLOY.md 를 참고하세요."
echo ""
