#!/usr/bin/env bash
# Copy in the backoff-and-jitter implementation and restart API/worker.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$LAB_DIR/../.." && pwd)"

compose() {
    if docker compose version >/dev/null 2>&1; then
        docker compose -f "$LAB_DIR/docker-compose.yml" "$@"
    else
        docker-compose -f "$LAB_DIR/docker-compose.yml" "$@"
    fi
}

log_info "Applying bounded retry backoff and jitter implementation"
cp "$LAB_DIR/after/docuask/api/dependencies/llm.py" \
    "$ROOT_DIR/docuask/api/dependencies/llm.py"
cp "$LAB_DIR/after/docuask/worker/tasks.py" \
    "$ROOT_DIR/docuask/worker/tasks.py"

cd "$LAB_DIR"
compose restart api worker

log_info "Retry fix applied. Run: make load-test"
