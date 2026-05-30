#!/usr/bin/env bash
# Send repeated question requests and report latency behavior.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

API_URL="${API_URL:-http://localhost:8080}"
REQUESTS="${REQUESTS:-5}"
MAX_ALLOWED_SECONDS="${MAX_ALLOWED_SECONDS:-3.5}"

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

log_info "Running $REQUESTS timed requests against $API_URL"

curl -fsS "$API_URL/api/health" >/dev/null

DOC_RESPONSE="$(
    curl -fsS -X POST "$API_URL/api/documents" \
        -H "Content-Type: application/json" \
        -d '{"title":"Timeout Load Test Doc","content":"Timeout load tests make repeated LLM calls so latency injection is visible."}'
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

slow_count=0
for index in $(seq 1 "$REQUESTS"); do
    result="$(
        curl -sS -o /tmp/docuask-lab2-load-response.json \
            -w "%{http_code} %{time_total}" \
            -X POST "$API_URL/api/questions" \
            -H "Content-Type: application/json" \
            -d "{\"question\":\"Request $index: what is this lab testing?\",\"document_id\":$DOC_ID}" || true
    )"
    http_code="${result%% *}"
    duration="${result##* }"
    log_info "request=$index status=$http_code duration=${duration}s"
    if ! compare_seconds "$duration" "$MAX_ALLOWED_SECONDS"; then
        slow_count=$((slow_count + 1))
    fi
done

if [[ "$slow_count" -gt 0 ]]; then
    log_error "$slow_count request(s) exceeded ${MAX_ALLOWED_SECONDS}s"
    log_error "This is expected before make apply-fix when latency is injected."
    exit 1
fi

log_info "All requests completed within ${MAX_ALLOWED_SECONDS}s"
