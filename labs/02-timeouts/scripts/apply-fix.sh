#!/usr/bin/env bash
# Copy in the explicit-timeout implementation and restart API/worker.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ROOT_DIR="$(cd "$LAB_DIR/../.." && pwd)"

compose() {
    if docker compose version >/dev/null 2>&1; then
        docker compose "$@"
    else
        docker-compose "$@"
    fi
}

log_info "Applying explicit LLM timeout implementation"
cp "$LAB_DIR/after/docuask/api/dependencies/llm.py" \
    "$ROOT_DIR/docuask/api/dependencies/llm.py"
cp "$LAB_DIR/after/docuask/worker/tasks.py" \
    "$ROOT_DIR/docuask/worker/tasks.py"

cd "$LAB_DIR"
compose restart api worker

log_info "Timeout fix applied. Run: make load-test"
