"""Static contract tests for Lab 4 idempotency assets."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import yaml


LAB_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = LAB_DIR.parents[1]


def read(path: str) -> str:
    return (LAB_DIR / path).read_text()


def read_repo(path: str) -> str:
    return (REPO_ROOT / path).read_text()


def load_mock_server() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "lab4_mock_llm_server",
        LAB_DIR / "mock-llm/server.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_before_route_creates_unconditionally_without_idempotency() -> None:
    before = read("before/docuask/api/routes/documents.py")

    assert "Idempotency-Key" not in before
    assert "IdempotencyKey" not in before
    assert "on_conflict" not in before
    assert "db.add(document)" in before


def test_after_route_uses_idempotency_key_and_dedupe_table() -> None:
    after = read("after/docuask/api/routes/documents.py")

    assert 'alias="Idempotency-Key"' in after
    assert "hashlib.sha256" in after
    assert "request_hash" in after
    assert 'on_conflict_do_nothing(index_elements=["key"])' in after
    assert "from docuask.models import" in after
    assert "IdempotencyKey" in after
    assert 'response.headers["Idempotent-Replay"] = "true"' in after
    assert "status.HTTP_409_CONFLICT" in after
    assert "status.HTTP_200_OK" in after
