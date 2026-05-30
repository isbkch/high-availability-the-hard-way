#!/usr/bin/env bash
# Start all services for the baseline lab.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

compose() {
    if docker compose version >/dev/null 2>&1; then
        docker compose "$@"
    else
        docker-compose "$@"
    fi
}

log_info "Starting Lab 1: Baseline Application"
check_docker

cd "$SCRIPT_DIR/.."
compose up -d --build

wait_for_service localhost 8080 "DocuAsk API" 90
wait_for_service localhost 5432 "PostgreSQL" 60
wait_for_service localhost 6379 "Redis" 60
wait_for_service localhost 8888 "Mock LLM" 60
wait_for_service localhost 9090 "Prometheus" 60
wait_for_service localhost 3001 "Grafana" 90

if compose ps --status running --services worker 2>/dev/null | grep -qx "worker"; then
    log_info "worker container is running"
elif compose ps worker 2>/dev/null | grep -Eiq "(up|running)"; then
    log_info "worker container is running"
else
    log_error "worker container is not running"
    compose logs --tail=100 worker || true
    exit 1
fi

log_info "Lab 1 is running."
log_info "API: http://localhost:8080"
log_info "Grafana: http://localhost:3001 (admin/admin)"
log_info "Run: make smoke-test"
