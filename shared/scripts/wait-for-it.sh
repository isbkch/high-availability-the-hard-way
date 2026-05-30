#!/usr/bin/env bash
# Wait until a TCP host:port is reachable, then optionally run a command.

set -euo pipefail

WAITFORIT_WAIT_SECONDS=${WAITFORIT_WAIT_SECONDS:-1}
WAITFORIT_TIMEOUT=${WAITFORIT_TIMEOUT:-30}
WAITFORIT_HOST=${WAITFORIT_HOST:-}
WAITFORIT_PORT=${WAITFORIT_PORT:-}
WAITFORIT_QUIET=${WAITFORIT_QUIET:-0}

usage() {
    echo "Usage: $0 host:port [-t timeout] [-q] [-- command args...]" >&2
}

log() {
    if [[ "$WAITFORIT_QUIET" != "1" ]]; then
        echo "$1"
    fi
}

if [[ $# -gt 0 && "$1" != -* ]]; then
    target="$1"
    shift
    WAITFORIT_HOST="${target%:*}"
    WAITFORIT_PORT="${target##*:}"
fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--timeout)
            WAITFORIT_TIMEOUT="$2"
            shift 2
            ;;
        -q|--quiet)
            WAITFORIT_QUIET=1
            shift
            ;;
        --)
            shift
            break
            ;;
        *)
            usage
            exit 2
            ;;
    esac
done

if [[ -z "$WAITFORIT_HOST" || -z "$WAITFORIT_PORT" || "$WAITFORIT_HOST" == "$WAITFORIT_PORT" ]]; then
    usage
    exit 2
fi

log "waiting ${WAITFORIT_TIMEOUT} seconds for ${WAITFORIT_HOST}:${WAITFORIT_PORT}..."

start_ts=$(date +%s)
while true; do
    if (echo > "/dev/tcp/${WAITFORIT_HOST}/${WAITFORIT_PORT}") >/dev/null 2>&1; then
        end_ts=$(date +%s)
        log "${WAITFORIT_HOST}:${WAITFORIT_PORT} is available after $((end_ts - start_ts)) seconds"
        break
    fi

    end_ts=$(date +%s)
    if [[ "$WAITFORIT_TIMEOUT" -gt 0 && $((end_ts - start_ts)) -ge "$WAITFORIT_TIMEOUT" ]]; then
        echo "timeout occurred after waiting ${WAITFORIT_TIMEOUT} seconds for ${WAITFORIT_HOST}:${WAITFORIT_PORT}" >&2
        exit 1
    fi

    sleep "$WAITFORIT_WAIT_SECONDS"
done

if [[ $# -gt 0 ]]; then
    exec "$@"
fi
