#!/usr/bin/env bash
# Enable deterministic intermittent LLM 503s.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

MOCK_LLM_URL="${MOCK_LLM_URL:-http://localhost:8888}"
FAILURE_MODE="${FAILURE_MODE:-alternating_503}"

log_info "Enabling ${FAILURE_MODE} failures in the Lab 3 mock LLM"

curl -fsS -X POST "$MOCK_LLM_URL/control/failure-mode" \
    -H "Content-Type: application/json" \
    -d "{\"mode\":\"${FAILURE_MODE}\",\"every_n\":2}" >/dev/null

log_info "Intermittent 503s enabled. Run: make load-test"
