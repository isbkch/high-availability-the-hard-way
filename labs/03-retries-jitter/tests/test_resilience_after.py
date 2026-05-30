"""Runtime contract for the Lab 3 after state.

These tests are intended for a running lab environment after `make apply-fix`.
They are skipped by default so static CI can validate the repository without
needing Docker.
"""

from __future__ import annotations

import os
import time
from typing import Any

import httpx
import pytest


API_URL = os.environ.get("API_URL", "http://localhost:8080")
MOCK_LLM_URL = os.environ.get("MOCK_LLM_URL", "http://localhost:8888")
MAX_ALLOWED_SECONDS = float(os.environ.get("MAX_ALLOWED_SECONDS", "8.0"))
RUN_RUNTIME = os.environ.get("RUN_LAB_RUNTIME_TESTS") == "1"
BROWNOUT_SECONDS = float(os.environ.get("BROWNOUT_SECONDS", "0.45"))


pytestmark = pytest.mark.skipif(
    not RUN_RUNTIME,
    reason="set RUN_LAB_RUNTIME_TESTS=1 with Lab 3 running to execute",
)


def create_completed_document(client: httpx.Client) -> int:
    response = client.post(
        f"{API_URL}/api/documents",
        json={
            "title": "Lab 3 After Runtime Contract",
            "content": (
                "Backoff and jitter spread retries so a short transient brownout "
                "does not consume the whole retry budget."
            ),
        },
    )
    response.raise_for_status()
    document_id = response.json()["id"]

    for _ in range(20):
        detail = client.get(f"{API_URL}/api/documents/{document_id}")
        detail.raise_for_status()
        if detail.json()["status"] == "completed":
            return document_id
        time.sleep(0.5)

    pytest.fail("document did not complete before retry budget check")


def enable_brownout(client: httpx.Client) -> None:
    response = client.post(
        f"{MOCK_LLM_URL}/control/failure-mode",
        json={
            "mode": "brownout_503",
            "every_n": 2,
            "brownout_seconds": BROWNOUT_SECONDS,
        },
    )
    response.raise_for_status()


def mock_state(client: httpx.Client) -> dict[str, Any]:
    response = client.get(f"{MOCK_LLM_URL}/mock-state")
    response.raise_for_status()
    return response.json()


def test_question_returns_successfully_within_retry_budget_after_jitter_fix() -> None:
    with httpx.Client(timeout=MAX_ALLOWED_SECONDS + 2) as client:
        client.post(f"{MOCK_LLM_URL}/control/reset").raise_for_status()
        document_id = create_completed_document(client)
        enable_brownout(client)

        started = time.perf_counter()
        response = client.post(
            f"{API_URL}/api/questions",
            json={
                "question": "What does the retry budget protect?",
                "document_id": document_id,
            },
        )
        elapsed = time.perf_counter() - started
        state = mock_state(client)

    assert response.status_code == 200
    assert elapsed <= MAX_ALLOWED_SECONDS
    assert state["failure_counter"] >= 1
    assert state["request_counter"] > state["failure_counter"]
