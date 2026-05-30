#!/usr/bin/env bash
# Show Lab 1 service logs.

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

cd "$SCRIPT_DIR/.."
if [[ "$#" -gt 0 ]]; then
    compose logs -f --tail=100 "$@"
else
    compose logs -f --tail=100 api worker
fi
