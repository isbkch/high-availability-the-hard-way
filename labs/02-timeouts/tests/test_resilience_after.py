"""Runtime contract for the Lab 2 after state.

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
MAX_ALLOWED_SECONDS = float(os.environ.get("MAX_ALLOWED_SECONDS", "3.5"))
RUN_RUNTIME = os.environ.get("RUN_LAB_RUNTIME_TESTS") == "1"


pytestmark = pytest.mark.skipif(
    not RUN_RUNTIME,
    reason="set RUN_LAB_RUNTIME_TESTS=1 with Lab 2 running to execute",
)


def test_question_returns_or_fails_fast_after_timeout_fix() -> None:
    started = time.perf_counter()
    response = httpx.post(
        f"{API_URL}/api/questions",
        json={"question": "What does the timeout lab demonstrate?"},
        timeout=MAX_ALLOWED_SECONDS + 2,
    )
    elapsed = time.perf_counter() - started

    assert response.status_code in {200, 500, 503}
    assert elapsed <= MAX_ALLOWED_SECONDS
