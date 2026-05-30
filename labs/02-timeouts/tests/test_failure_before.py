"""Runtime contract for the Lab 2 before state.

These tests are intended for a running lab environment after `make break`.
They are skipped by default so static CI can validate the repository without
needing Docker.
"""

from __future__ import annotations

import os
import time

import httpx
import pytest


API_URL = os.environ.get("API_URL", "http://localhost:8080")
LATENCY_MS = int(os.environ.get("LATENCY_MS", "5000"))
RUN_RUNTIME = os.environ.get("RUN_LAB_RUNTIME_TESTS") == "1"


pytestmark = pytest.mark.skipif(
    not RUN_RUNTIME,
    reason="set RUN_LAB_RUNTIME_TESTS=1 with Lab 2 running to execute",
)


def test_question_waits_with_no_timeout_before_fix() -> None:
    started = time.perf_counter()
    response = httpx.post(
        f"{API_URL}/api/questions",
        json={"question": "What does the timeout lab demonstrate?"},
        timeout=(LATENCY_MS / 1000) + 10,
    )
    elapsed = time.perf_counter() - started

    assert response.status_code in {200, 500, 503}
    assert elapsed >= (LATENCY_MS / 1000) * 0.8
