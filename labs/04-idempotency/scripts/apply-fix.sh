#!/usr/bin/env bash
# Copy in the idempotent document route and restart the API.

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

log_info "Applying the idempotent document route"
cp "$LAB_DIR/after/docuask/api/routes/documents.py" \
    "$ROOT_DIR/docuask/api/routes/documents.py"

cd "$LAB_DIR"
compose restart api worker

log_info "Idempotency fix applied. Run: make load-test"
