#!/usr/bin/env bash
# Restore the non-idempotent route and clear the dedupe table.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$LAB_DIR/../.." && pwd)"
SKIP_COMPOSE="${1:-}"
MOCK_LLM_URL="${MOCK_LLM_URL:-http://localhost:8888}"

compose() {
    if docker compose version >/dev/null 2>&1; then
        docker compose -f "$LAB_DIR/docker-compose.yml" "$@"
    else
        docker-compose -f "$LAB_DIR/docker-compose.yml" "$@"
    fi
}

copy_impl() {
    cp "$LAB_DIR/before/docuask/api/routes/documents.py" \
        "$ROOT_DIR/docuask/api/routes/documents.py"
}

clear_dedupe_table() {
    compose exec -T postgres psql -U docuask -d docuask \
        -c "TRUNCATE TABLE idempotency_keys;" >/dev/null 2>&1 || true
}

disable_failures() {
    curl -fsS -X POST "$MOCK_LLM_URL/control/reset" >/dev/null 2>&1 || true
}

log_info "Restoring Lab 4 before implementation"
copy_impl

if [[ "$SKIP_COMPOSE" != "--skip-compose" ]]; then
    clear_dedupe_table
    disable_failures
    cd "$LAB_DIR"
    compose restart api worker
fi

log_info "Lab 4 reset complete"
