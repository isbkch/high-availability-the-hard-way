"""Runtime contract for the Lab 4 before state.

Run against a running lab with the before route active. Skipped by default so
static CI can validate the repository without Docker.
"""

from __future__ import annotations

import os
import uuid

import httpx
import pytest


API_URL = os.environ.get("API_URL", "http://localhost:8080")
RUN_RUNTIME = os.environ.get("RUN_LAB_RUNTIME_TESTS") == "1"
RETRIES = int(os.environ.get("RETRIES", "4"))


pytestmark = pytest.mark.skipif(
    not RUN_RUNTIME,
    reason="set RUN_LAB_RUNTIME_TESTS=1 with Lab 4 (before) running to execute",
)


def test_retried_submissions_create_duplicate_documents_before_fix() -> None:
    key = f"lab4-before-{uuid.uuid4()}"
    body = {
        "title": "Lab 4 Before Runtime Contract",
        "content": "A retrying client submits this identical document several times.",
    }

    ids: list[int] = []
    with httpx.Client(timeout=10) as client:
        for _ in range(RETRIES):
            response = client.post(
                f"{API_URL}/api/documents",
                headers={"Idempotency-Key": key},
                json=body,
            )
            response.raise_for_status()
            ids.append(response.json()["id"])

    # Before the fix the Idempotency-Key is ignored: every retry creates a row.
    assert len(set(ids)) == RETRIES
