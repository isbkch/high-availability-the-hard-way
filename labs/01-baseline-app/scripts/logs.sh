#!/usr/bin/env bash
# Show Lab 1 service logs.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"
LAB_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

compose() {
    if docker compose version >/dev/null 2>&1; then
        docker compose -f "$LAB_DIR/docker-compose.yml" "$@"
    else
        docker-compose -f "$LAB_DIR/docker-compose.yml" "$@"
    fi
}

cd "$LAB_DIR"
if [[ "$#" -gt 0 ]]; then
    compose logs -f --tail=100 "$@"
else
    compose logs -f --tail=100 api worker
fi
