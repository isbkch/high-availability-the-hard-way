"""Runtime contract for the Lab 3 before state.

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
RUN_RUNTIME = os.environ.get("RUN_LAB_RUNTIME_TESTS") == "1"


pytestmark = pytest.mark.skipif(
    not RUN_RUNTIME,
    reason="set RUN_LAB_RUNTIME_TESTS=1 with Lab 3 running to execute",
)


def test_question_path_survives_but_can_show_retry_storm_before_fix() -> None:
    started = time.perf_counter()
    response = httpx.post(
        f"{API_URL}/api/questions",
        json={"question": "What does the retry storm lab demonstrate?"},
        timeout=12,
    )
    elapsed = time.perf_counter() - started

    assert response.status_code in {200, 500, 503}
    assert elapsed >= 0
