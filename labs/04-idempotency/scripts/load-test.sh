#!/usr/bin/env bash
# Submit the same document repeatedly and report duplicate-creation behavior.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

API_URL="${API_URL:-http://localhost:8080}"
MOCK_LLM_URL="${MOCK_LLM_URL:-http://localhost:8888}"
RETRIES="${RETRIES:-4}"

json_field() {
    python3 - "$1" "$2" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
for part in sys.argv[2].split("."):
    payload = payload[part]
print(payload)
PY
}

log_info "Submitting the same document $RETRIES times against $API_URL"

curl -fsS "$API_URL/api/health" >/dev/null
curl -fsS -X POST "$MOCK_LLM_URL/control/reset" >/dev/null

IDEMPOTENCY_KEY="lab4-$(date +%s)-$$"
BODY='{"title":"Idempotency Load Test Doc","content":"A retrying client submits this identical document several times."}'

declare -a returned_ids=()
for index in $(seq 1 "$RETRIES"); do
    result="$(
        curl -sS -o /tmp/docuask-lab4-load-response.json \
            -w "%{http_code}" \
            -X POST "$API_URL/api/documents" \
            -H "Content-Type: application/json" \
            -H "Idempotency-Key: $IDEMPOTENCY_KEY" \
            -d "$BODY" || true
    )"
    doc_id="$(json_field "$(cat /tmp/docuask-lab4-load-response.json)" id 2>/dev/null || echo "")"
    returned_ids+=("$doc_id")
    log_info "submission=$index status=$result document_id=$doc_id"
done

distinct_ids="$(printf '%s\n' "${returned_ids[@]}" | sort -u | grep -c .)"
state="$(curl -fsS "$MOCK_LLM_URL/mock-state")"
embedding_requests="$(json_field "$state" embedding_requests)"

log_info "distinct_document_ids=$distinct_ids embedding_requests=$embedding_requests"

if [[ "$distinct_ids" -ne 1 ]]; then
    log_error "$RETRIES identical submissions created $distinct_ids documents."
    log_error "Before make apply-fix, retries without idempotency duplicate work and cost."
    exit 1
fi

log_info "All $RETRIES submissions collapsed to a single document. Idempotency works."
