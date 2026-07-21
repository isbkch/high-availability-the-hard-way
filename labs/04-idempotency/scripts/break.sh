#!/usr/bin/env bash
# Arm the retry scenario: reset mock counters and announce duplicate submissions.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

MOCK_LLM_URL="${MOCK_LLM_URL:-http://localhost:8888}"
RETRIES="${RETRIES:-4}"

log_info "Arming the idempotency scenario"
curl -fsS -X POST "$MOCK_LLM_URL/control/reset" >/dev/null

log_warn "The load test will submit the SAME document ${RETRIES} times with one Idempotency-Key,"
log_warn "exactly as a client retrying after a timeout would. Run: make load-test"
