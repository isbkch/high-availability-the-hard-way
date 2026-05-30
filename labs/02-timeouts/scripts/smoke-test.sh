#!/usr/bin/env bash
# Run smoke tests against the timeout lab.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

API_URL="${API_URL:-http://localhost:8080}"

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

json_len() {
    python3 - "$1" "$2" <<'PY'
import json
import sys

payload = json.loads(sys.argv[1])
for part in sys.argv[2].split("."):
    payload = payload[part]
print(len(payload))
PY
}

require_label() {
    case "$1" in
        healthy|degraded|unhealthy) ;;
        *)
            log_error "Unexpected health label '$1'"
            exit 1
            ;;
    esac
}

log_info "Running Lab 2 smoke tests against $API_URL"

HEALTH="$(curl -fsS "$API_URL/api/health")"
STATUS="$(json_field "$HEALTH" status)"
DATABASE="$(json_field "$HEALTH" database)"
REDIS="$(json_field "$HEALTH" redis)"
LLM="$(json_field "$HEALTH" llm)"

require_label "$STATUS"
require_label "$DATABASE"
require_label "$REDIS"
require_label "$LLM"

if [[ "$STATUS" != "healthy" ]]; then
    log_error "Expected timeout lab health status healthy, got $STATUS: $HEALTH"
    exit 1
fi

DOC_RESPONSE="$(
    curl -fsS -X POST "$API_URL/api/documents" \
        -H "Content-Type: application/json" \
        -d '{"title":"Timeout Smoke Test Doc","content":"Timeout smoke tests verify upload, worker embedding, and Q&A through Toxiproxy."}'
)"
DOC_ID="$(json_field "$DOC_RESPONSE" id)"

if [[ -z "$DOC_ID" ]]; then
    log_error "Document upload did not return an id: $DOC_RESPONSE"
    exit 1
fi
log_info "Document upload succeeded with id $DOC_ID"

for _ in 1 2 3 4 5 6 7 8 9 10; do
    DOC_DETAIL="$(curl -fsS "$API_URL/api/documents/$DOC_ID")"
    DOC_STATUS="$(json_field "$DOC_DETAIL" status)"
    if [[ "$DOC_STATUS" == "completed" ]]; then
        break
    fi
    sleep 1
done

if [[ "$DOC_STATUS" != "completed" ]]; then
    log_error "Document $DOC_ID was not processed by the worker. Last status: $DOC_STATUS"
    exit 1
fi
log_info "Worker processed document $DOC_ID"

QUESTION_RESPONSE="$(
    curl -fsS -X POST "$API_URL/api/questions" \
        -H "Content-Type: application/json" \
        -d "{\"question\":\"What do timeout smoke tests verify?\",\"document_id\":$DOC_ID}"
)"
ANSWER="$(json_field "$QUESTION_RESPONSE" answer)"
SOURCE_COUNT="$(json_len "$QUESTION_RESPONSE" sources)"

if [[ -z "$ANSWER" ]]; then
    log_error "Question response did not include an answer: $QUESTION_RESPONSE"
    exit 1
fi
if [[ "$SOURCE_COUNT" -lt 1 ]]; then
    log_error "Question response did not include processed document sources: $QUESTION_RESPONSE"
    exit 1
fi

log_info "All Lab 2 smoke tests passed"
