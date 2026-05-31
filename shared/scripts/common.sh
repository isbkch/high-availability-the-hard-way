#!/usr/bin/env bash
# Common functions for lab scripts

set -euo pipefail

COMMON_SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$COMMON_SCRIPT_DIR/../.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
}

wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout_seconds=${4:-60}
    local start_ts
    local now_ts

    log_info "Waiting for $service_name ($host:$port)..."
    start_ts=$(date +%s)
    while true; do
        if (echo > "/dev/tcp/$host/$port") >/dev/null 2>&1; then
            log_info "$service_name is ready!"
            return 0
        fi

        now_ts=$(date +%s)
        if [[ $((now_ts - start_ts)) -ge "$timeout_seconds" ]]; then
            log_error "$service_name failed to start within $timeout_seconds seconds"
            exit 1
        fi

        sleep 1
    done
}
