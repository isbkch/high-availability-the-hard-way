#!/usr/bin/env bash
# Use this script to test if a TCP connection to a given host/port is available

WAITFORIT_WAIT_SECONDS=${WAITFORIT_WAIT_SECONDS:-15}
WAITFORIT_TIMEOUT=${WAITFORIT_TIMEOUT:-30}
WAITFORIT_HOST=${WAITFORIT_HOST:-}
WAITFORIT_PORT=${WAITFORIT_PORT:-}
WAITFORIT_STRICT=${WAITFORIT_STRICT:-}
WAITFORIT_CHILD=${WAITFORIT_CHILD:-}
WAITFORIT_QUIET=${WAITFORIT_QUIET:-}

if [[ "$WAITFORIT_QUIET" -eq 1 ]]; then
    QUIET_FLAG="-q"
else
    QUIET_FLAG=""
fi

if [[ "$WAITFORIT_TIMEOUT" -gt 0 ]]; then
    echo "waiting $WAITFORIT_TIMEOUT seconds for $WAITFORIT_HOST:$WAITFORIT_PORT..."
else
    echo "waiting for $WAITFORIT_HOST:$WAITFORIT_PORT without a timeout"
fi

start_ts=$(date +%s)
while :
do
    if [[ $WAITFORIT_ISBUSY -eq 1 ]]; then
        nc -z $WAITFORIT_HOST $WAITFORIT_PORT
        RESULT=$?
    else
        (echo > /dev/tcp/$WAITFORIT_HOST/$WAITFORIT_PORT) >/dev/null 2>&1
        RESULT=$?
    fi

    if [[ $RESULT -eq 0 ]]; then
        end_ts=$(date +%s)
        echo "$WAITFORIT_HOST:$WAITFORIT_PORT is available after $((end_ts - start_ts)) seconds"
        break
    fi

    if [[ $WAITFORIT_TIMEOUT -gt 0 ]]; then
        end_ts=$(date +%s)
        if [[ $((end_ts - start_ts)) -ge $WAITFORIT_TIMEOUT ]]; then
            echo "timeout occurred after waiting $WAITFORIT_TIMEOUT seconds for $WAITFORIT_HOST:$WAITFORIT_PORT"
            exit 1
        fi
    fi

    sleep $WAITFORIT_WAIT_SECONDS
done

exec "$WAITFORIT_CHILD"
