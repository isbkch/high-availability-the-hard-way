#!/usr/bin/env bash
# Send repeated question requests and report retry-storm behavior.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

API_URL="${API_URL:-http://localhost:8080}"
MOCK_LLM_URL="${MOCK_LLM_URL:-http://localhost:8888}"
REQUESTS="${REQUESTS:-8}"
MAX_ALLOWED_SECONDS="${MAX_ALLOWED_SECONDS:-8.0}"

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

compare_seconds() {
    python3 - "$1" "$2" <<'PY'
import sys

actual = float(sys.argv[1])
limit = float(sys.argv[2])
sys.exit(0 if actual <= limit else 1)
PY
}

log_info "Running $REQUESTS retry-budget requests against $API_URL"

curl -fsS "$API_URL/api/health" >/dev/null

DOC_RESPONSE="$(
    curl -fsS -X POST "$API_URL/api/documents" \
        -H "Content-Type: application/json" \
        -d '{"title":"Retries Load Test Doc","content":"Retries load tests make repeated LLM calls so retry storms and jitter are visible."}'
)"
DOC_ID="$(json_field "$DOC_RESPONSE" id)"

for _ in 1 2 3 4 5 6 7 8 9 10; do
    DOC_DETAIL="$(curl -fsS "$API_URL/api/documents/$DOC_ID")"
    DOC_STATUS="$(json_field "$DOC_DETAIL" status)"
    if [[ "$DOC_STATUS" == "completed" || "$DOC_STATUS" == "failed" ]]; then
        break
    fi
    sleep 1
done

log_info "Document $DOC_ID processing status: $DOC_STATUS"

retry_budget_exceeded_count=0
retry_storm_status_count=0
bad_status_count=0
for index in $(seq 1 "$REQUESTS"); do
    result="$(
        curl -sS -o /tmp/docuask-lab3-load-response.json \
            -w "%{http_code} %{time_total}" \
            -X POST "$API_URL/api/questions" \
            -H "Content-Type: application/json" \
            -d "{\"question\":\"Request $index: what is this lab testing?\",\"document_id\":$DOC_ID}" || true
    )"
    http_code="${result%% *}"
    duration="${result##* }"
    state="$(curl -fsS "$MOCK_LLM_URL/mock-state")"
    request_counter="$(json_field "$state" request_counter)"
    failure_counter="$(json_field "$state" failure_counter)"
    log_info "request=$index status=$http_code duration=${duration}s llm_requests=$request_counter llm_503s=$failure_counter"

    case "$http_code" in
        200|500|503) ;;
        *)
            bad_status_count=$((bad_status_count + 1))
            ;;
    esac
    if [[ "$http_code" == "500" || "$http_code" == "503" ]]; then
        retry_budget_exceeded_count=$((retry_budget_exceeded_count + 1))
    fi
    if ! compare_seconds "$duration" "$MAX_ALLOWED_SECONDS"; then
        retry_storm_status_count=$((retry_storm_status_count + 1))
    fi
done

if [[ "$bad_status_count" -gt 0 ]]; then
    log_error "$bad_status_count request(s) returned an unexpected HTTP status"
    exit 1
fi

if [[ "$retry_storm_status_count" -gt 0 ]]; then
    log_error "$retry_storm_status_count request(s) exceeded ${MAX_ALLOWED_SECONDS}s"
    log_error "Before make apply-fix, immediate retries can align into a retry storm."
    exit 1
fi

log_info "retry_budget_exceeded_count=$retry_budget_exceeded_count"
log_info "All requests stayed within the visible retry budget"
