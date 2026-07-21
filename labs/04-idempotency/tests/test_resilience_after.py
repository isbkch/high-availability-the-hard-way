"""Runtime contract for the Lab 4 after state.

Run against a running lab with the after (idempotent) route active. Skipped by
default so static CI can validate the repository without Docker.
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
    reason="set RUN_LAB_RUNTIME_TESTS=1 with Lab 4 (after) running to execute",
)


def test_retried_submissions_collapse_to_one_document_after_fix() -> None:
    key = f"lab4-after-{uuid.uuid4()}"
    body = {
        "title": "Lab 4 After Runtime Contract",
        "content": "A retrying client submits this identical document several times.",
    }

    ids: list[int] = []
    replays = 0
    with httpx.Client(timeout=10) as client:
        for attempt in range(RETRIES):
            response = client.post(
                f"{API_URL}/api/documents",
                headers={"Idempotency-Key": key},
                json=body,
            )
            response.raise_for_status()
            ids.append(response.json()["id"])
            if attempt == 0:
                assert response.status_code == 201
            else:
                assert response.status_code == 200
                assert response.headers.get("Idempotent-Replay") == "true"
                replays += 1

    assert len(set(ids)) == 1
    assert replays == RETRIES - 1


def test_same_key_different_body_returns_409_after_fix() -> None:
    key = f"lab4-conflict-{uuid.uuid4()}"
    with httpx.Client(timeout=10) as client:
        first = client.post(
            f"{API_URL}/api/documents",
            headers={"Idempotency-Key": key},
            json={"title": "Original", "content": "original body"},
        )
        first.raise_for_status()

        conflict = client.post(
            f"{API_URL}/api/documents",
            headers={"Idempotency-Key": key},
            json={"title": "Different", "content": "different body"},
        )

    assert conflict.status_code == 409
