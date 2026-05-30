#!/usr/bin/env bash
# Inject latency between DocuAsk and the mock LLM through Toxiproxy.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../../shared/scripts/common.sh"

TOXIPROXY_URL="${TOXIPROXY_URL:-http://localhost:8474}"
LATENCY_MS="${LATENCY_MS:-5000}"
JITTER_MS="${JITTER_MS:-250}"

log_info "Injecting ${LATENCY_MS}ms LLM latency through Toxiproxy"

curl -fsS -X DELETE "$TOXIPROXY_URL/proxies/mock-llm/toxics/llm-latency" \
    >/dev/null 2>&1 || true

curl -fsS -X POST "$TOXIPROXY_URL/proxies/mock-llm/toxics" \
    -H "Content-Type: application/json" \
    -d "{
          \"name\": \"llm-latency\",
          \"type\": \"latency\",
          \"stream\": \"downstream\",
          \"toxicity\": 1.0,
          \"attributes\": {
            \"latency\": ${LATENCY_MS},
            \"jitter\": ${JITTER_MS}
          }
        }" >/dev/null

log_info "Latency injected. Run: make load-test"
