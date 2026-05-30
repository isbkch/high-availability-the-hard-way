#!/usr/bin/env bash
# Reset the baseline lab to a clean state.

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

check_docker

cd "$SCRIPT_DIR/.."
log_info "Stopping Lab 1 and removing volumes"
compose down -v --remove-orphans

log_info "Starting a clean Lab 1 stack"
compose up -d --build

wait_for_service localhost 8080 "DocuAsk API" 90
log_info "Lab 1 reset complete. Run: make smoke-test"
