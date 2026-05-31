#!/usr/bin/env bash
# Restore the no-timeout implementation and remove injected latency.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$LAB_DIR/../.." && pwd)"
SKIP_COMPOSE="${1:-}"
TOXIPROXY_URL="${TOXIPROXY_URL:-http://localhost:8474}"

compose() {
    if docker compose version >/dev/null 2>&1; then
        docker compose -f "$LAB_DIR/docker-compose.yml" "$@"
    else
        docker-compose -f "$LAB_DIR/docker-compose.yml" "$@"
    fi
}

copy_impl() {
    cp "$LAB_DIR/before/docuask/api/dependencies/llm.py" \
        "$ROOT_DIR/docuask/api/dependencies/llm.py"
    cp "$LAB_DIR/before/docuask/worker/tasks.py" \
        "$ROOT_DIR/docuask/worker/tasks.py"
}

remove_latency() {
    curl -fsS -X DELETE "$TOXIPROXY_URL/proxies/mock-llm/toxics/llm-latency" \
        >/dev/null 2>&1 || true
}

log_info "Restoring Lab 2 before implementation"
copy_impl
remove_latency

if [[ "$SKIP_COMPOSE" != "--skip-compose" ]]; then
    cd "$LAB_DIR"
    compose restart api worker
fi

log_info "Lab 2 reset complete"
