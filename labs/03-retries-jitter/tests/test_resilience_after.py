"""Runtime contract for the Lab 3 after state.

These tests are intended for a running lab environment after `make apply-fix`.
They are skipped by default so static CI can validate the repository without
needing Docker.
"""

from __future__ import annotations

import os
import time

import httpx
import pytest


API_URL = os.environ.get("API_URL", "http://localhost:8080")
MAX_ALLOWED_SECONDS = float(os.environ.get("MAX_ALLOWED_SECONDS", "8.0"))
RUN_RUNTIME = os.environ.get("RUN_LAB_RUNTIME_TESTS") == "1"


pytestmark = pytest.mark.skipif(
    not RUN_RUNTIME,
    reason="set RUN_LAB_RUNTIME_TESTS=1 with Lab 3 running to execute",
)


def test_question_returns_within_retry_budget_after_jitter_fix() -> None:
    started = time.perf_counter()
    response = httpx.post(
        f"{API_URL}/api/questions",
        json={"question": "What does the retry budget protect?"},
        timeout=MAX_ALLOWED_SECONDS + 2,
    )
    elapsed = time.perf_counter() - started

    assert response.status_code in {200, 500, 503}
    assert elapsed <= MAX_ALLOWED_SECONDS
