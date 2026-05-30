"""Static contract tests for Lab 3 retries and jitter assets."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest
import yaml


LAB_DIR = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (LAB_DIR / path).read_text()


def load_mock_server() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "lab3_mock_llm_server",
        LAB_DIR / "mock-llm/server.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_before_client_retries_immediately_without_sleep_or_backoff() -> None:
    before = read("before/docuask/api/dependencies/llm.py")

    assert "MAX_RETRY_ATTEMPTS = 4" in before
    assert "for attempt in range(1, MAX_RETRY_ATTEMPTS + 1)" in before
    assert "response.status_code in RETRYABLE_STATUS_CODES" in before
    assert "asyncio.sleep" not in before
    assert "BACKOFF" not in before
    assert "JITTER" not in before


def test_after_client_uses_bounded_exponential_backoff_and_jitter() -> None:
    after = read("after/docuask/api/dependencies/llm.py")

    assert "MAX_RETRY_ATTEMPTS = 4" in after
    assert "RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}" in after
    assert "LLM_TIMEOUT = httpx.Timeout(" in after
    assert "RETRY_BASE_DELAY_SECONDS" in after
    assert "RETRY_MAX_DELAY_SECONDS" in after
    assert "RETRY_JITTER_SECONDS" in after
    assert "2 ** (attempt - 1)" in after
    assert "random.uniform(0.0, RETRY_JITTER_SECONDS)" in after
    assert "await asyncio.sleep(delay)" in after


def test_worker_before_after_artifacts_are_present_and_distinct() -> None:
    before_worker = read("before/docuask/worker/tasks.py")
    after_worker = read("after/docuask/worker/tasks.py")
    apply_fix = read("scripts/apply-fix.sh")
    reset = read("scripts/reset.sh")

    assert "MAX_EMBEDDING_RETRY_ATTEMPTS = 4" in before_worker
    assert "asyncio.sleep" not in before_worker
    assert "EMBEDDING_RETRY_BASE_DELAY_SECONDS" in after_worker
    assert "await asyncio.sleep(delay)" in after_worker
    assert "random.uniform(0.0, EMBEDDING_RETRY_JITTER_SECONDS)" in after_worker
    assert "after/docuask/worker/tasks.py" in apply_fix
    assert "before/docuask/worker/tasks.py" in reset


def test_compose_uses_lab_local_mock_failure_mode_and_runtime_copy() -> None:
    compose = yaml.safe_load(read("docker-compose.yml"))
    services = compose["services"]

    assert services["api"]["environment"]["LLM_API_BASE"] == "http://mock-llm:8888/v1"
    assert services["worker"]["environment"]["LLM_API_BASE"] == "http://mock-llm:8888/v1"
    assert "../../docuask:/app/docuask" in services["api"]["volumes"]
    assert "../../docuask:/app/docuask" in services["worker"]["volumes"]
    assert "./mock-llm:/app" in services["mock-llm"]["volumes"]
    assert "retry-mock" in services["api"]["environment"]["LLM_MODEL"]


def test_scripts_use_common_helpers_compose_fallback_and_failure_controls() -> None:
    for script in (LAB_DIR / "scripts").glob("*.sh"):
        text = script.read_text()
        assert "../../../shared/scripts/common.sh" in text
        if "compose()" in text:
            assert "docker compose" in text
            assert "docker-compose" in text

    break_script = read("scripts/break.sh")
    reset_script = read("scripts/reset.sh")
    load = read("scripts/load-test.sh")

    assert "/control/failure-mode" in break_script
    assert 'FAILURE_MODE="${FAILURE_MODE:-brownout_503}"' in break_script
    assert "BROWNOUT_SECONDS" in break_script
    assert '\\"mode\\"' in break_script
    assert "/control/reset" in reset_script
    assert "before/docuask/api/dependencies/llm.py" in reset_script
    assert "configure_failure_window" in load
    assert 'FAILURE_MODE="${FAILURE_MODE:-brownout_503}"' in load
    assert "BROWNOUT_SECONDS" in load
    assert "failed_response_count" in load
    assert "http_code" in load
    assert "500|503" not in load


def test_smoke_and_load_tests_use_current_api_routes() -> None:
    smoke = read("scripts/smoke-test.sh")
    load = read("scripts/load-test.sh")

    for route in (
        "/api/health",
        "/api/documents",
        "/api/questions",
    ):
        assert route in smoke
    assert "/api/health" in load
    assert "/api/questions" in load
    assert "/mock-state" in load
    assert "MAX_ALLOWED_SECONDS" in load


def test_mock_llm_has_deterministic_intermitent_503_controls() -> None:
    server = read("mock-llm/server.py")

    assert "/control/failure-mode" in server
    assert "/control/reset" in server
    assert "alternating_503" in server
    assert "every_nth_503" in server
    assert "brownout_503" in server
    assert "request_counter" in server
    assert "503" in server


def test_mock_llm_brownout_mode_models_transient_outage_window(monkeypatch: pytest.MonkeyPatch) -> None:
    server = load_mock_server()
    current_time = [100.0]

    class FakeTime:
        @staticmethod
        def monotonic() -> float:
            return current_time[0]

    monkeypatch.setattr(server, "time", FakeTime, raising=False)

    server.set_failure_mode(
        {
            "mode": "brownout_503",
            "every_n": 2,
            "brownout_seconds": 0.4,
        }
    )

    assert server.should_fail_request() is True
    assert server.snapshot_state()["failure_counter"] == 1

    current_time[0] += 0.5

    assert server.should_fail_request() is False
    assert server.snapshot_state()["request_counter"] == 2
    assert server.snapshot_state()["failure_counter"] == 1


def test_runtime_pytests_exist_for_before_and_after_contracts() -> None:
    before_test = read("tests/test_failure_before.py")
    after_test = read("tests/test_resilience_after.py")

    assert "RUN_LAB_RUNTIME_TESTS" in before_test
    assert "retry storm" in before_test
    assert "/api/documents" in before_test
    assert "/control/failure-mode" in before_test
    assert "/mock-state" in before_test
    assert "document_id" in before_test
    assert "assert response.status_code != 200" in before_test
    assert "MAX_ALLOWED_SECONDS" in after_test
    assert "retry budget" in after_test
    assert "/api/documents" in after_test
    assert "/control/failure-mode" in after_test
    assert "/mock-state" in after_test
    assert "document_id" in after_test
    assert "assert response.status_code == 200" in after_test
    assert "failure_counter" in after_test


def test_docs_and_dashboard_describe_retries_jitter_lab() -> None:
    readme = read("README.md")
    architecture = read("architecture.md")
    reflection = read("reflection.md")
    dashboard = json.loads(read("dashboards/grafana-dashboard.json"))

    assert "make break" in readme
    assert "make apply-fix" in readme
    assert "brownout_503" in readme
    assert "alternating_503" in readme
    assert "retry storm" in architecture
    assert "exponential backoff" in architecture
    assert "Root Cause" in reflection
    assert "Production Checklist" in reflection
    assert "Before" in reflection
    assert "After" in reflection
    assert "jitter" in reflection
    assert dashboard["title"] == "DocuAsk Lab 3 - Retries and Jitter"
