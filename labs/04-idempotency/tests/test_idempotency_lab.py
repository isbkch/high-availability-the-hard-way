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


def test_mock_llm_counts_requests_and_supports_reset() -> None:
    server = read("mock-llm/server.py")

    assert "/v1/models" in server
    assert "/v1/embeddings" in server
    assert "/v1/chat/completions" in server
    assert "/mock-state" in server
    assert "/control/reset" in server
    assert "request_counter" in server


def test_mock_llm_reset_zeroes_the_counter() -> None:
    server = load_mock_server()

    server.reset_state()
    server.bump("embedding_requests")
    server.bump("chat_requests")
    assert server.snapshot_state()["request_counter"] == 2

    server.reset_state()
    assert server.snapshot_state()["request_counter"] == 0
    assert server.snapshot_state()["embedding_requests"] == 0


def test_compose_mounts_shared_docuask_and_has_no_toxiproxy() -> None:
    compose = yaml.safe_load(read("docker-compose.yml"))
    services = compose["services"]

    assert "toxiproxy" not in services
    assert services["api"]["environment"]["LLM_API_BASE"] == "http://mock-llm:8888/v1"
    assert services["worker"]["environment"]["LLM_API_BASE"] == "http://mock-llm:8888/v1"
    assert "../../docuask:/app/docuask" in services["api"]["volumes"]
    assert "../../docuask:/app/docuask" in services["worker"]["volumes"]
    assert "./mock-llm:/app" in services["mock-llm"]["volumes"]


def test_makefile_pins_lab_compose_file() -> None:
    makefile = read("Makefile")
    assert "-f docker-compose.yml" in makefile


def test_dashboard_titled_for_lab_4() -> None:
    dashboard = json.loads(read("dashboards/grafana-dashboard.json"))
    assert dashboard["title"] == "DocuAsk Lab 4 - Idempotency"


def test_scripts_use_common_helpers_and_compose_fallback() -> None:
    for script in (LAB_DIR / "scripts").glob("*.sh"):
        text = script.read_text()
        assert "../../../shared/scripts/common.sh" in text
        if "compose()" in text:
            assert "docker compose" in text
            assert "docker-compose" in text
            assert '-f "$LAB_DIR/docker-compose.yml"' in text


def test_apply_fix_and_reset_swap_the_document_route() -> None:
    apply_fix = read("scripts/apply-fix.sh")
    reset = read("scripts/reset.sh")

    assert "after/docuask/api/routes/documents.py" in apply_fix
    assert "before/docuask/api/routes/documents.py" in reset
    assert "TRUNCATE" in reset
    assert "idempotency_keys" in reset


def test_break_resets_mock_and_load_test_counts_distinct_ids() -> None:
    break_script = read("scripts/break.sh")
    load = read("scripts/load-test.sh")

    assert "/control/reset" in break_script
    assert "Idempotency-Key" in load
    assert "/mock-state" in load
    assert "distinct" in load


def test_smoke_and_load_use_current_api_routes() -> None:
    smoke = read("scripts/smoke-test.sh")
    load = read("scripts/load-test.sh")

    for route in ("/api/health", "/api/documents"):
        assert route in smoke
    assert "/api/documents" in load


def test_docs_describe_idempotency_lab() -> None:
    readme = read("README.md")
    architecture = read("architecture.md")
    reflection = read("reflection.md")

    assert "make break" in readme
    assert "make apply-fix" in readme
    assert "Idempotency-Key" in readme
    assert "Idempotency-Key" in architecture
    assert "on_conflict" in architecture or "ON CONFLICT" in architecture
    assert "Root Cause" in reflection
    assert "Production Checklist" in reflection
    assert "Before" in reflection
    assert "After" in reflection
    assert "idempotency" in reflection.lower()


def test_runtime_pytests_exist_for_before_and_after() -> None:
    before_test = read("tests/test_failure_before.py")
    after_test = read("tests/test_resilience_after.py")

    assert "RUN_LAB_RUNTIME_TESTS" in before_test
    assert "Idempotency-Key" in before_test
    assert "/api/documents" in before_test
    assert "RUN_LAB_RUNTIME_TESTS" in after_test
    assert "Idempotency-Key" in after_test
    assert "Idempotent-Replay" in after_test
    assert "409" in after_test
