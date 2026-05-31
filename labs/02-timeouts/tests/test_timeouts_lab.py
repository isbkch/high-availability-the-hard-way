"""Static contract tests for Lab 2 timeout assets."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


LAB_DIR = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (LAB_DIR / path).read_text()


def test_before_client_has_no_explicit_httpx_timeout() -> None:
    before = read("before/docuask/api/dependencies/llm.py")

    assert "httpx.AsyncClient(timeout=None)" in before
    assert "httpx.Timeout" not in before


def test_worker_before_after_artifacts_are_present() -> None:
    before_worker = read("before/docuask/worker/tasks.py")
    after_worker = read("after/docuask/worker/tasks.py")
    apply_fix = read("scripts/apply-fix.sh")
    reset = read("scripts/reset.sh")

    assert "httpx.AsyncClient(timeout=None)" in before_worker
    assert "httpx.Timeout(" in after_worker
    assert "after/docuask/worker/tasks.py" in apply_fix
    assert "before/docuask/worker/tasks.py" in reset
    assert "httpx.Timeout" not in before_worker


def test_after_client_uses_explicit_timeout_budget() -> None:
    after = read("after/docuask/api/dependencies/llm.py")

    assert "LLM_TIMEOUT = httpx.Timeout(" in after
    assert "connect=" in after
    assert "read=" in after
    assert "write=" in after
    assert "pool=" in after
    assert "httpx.AsyncClient(timeout=LLM_TIMEOUT)" in after
    assert "httpx.TimeoutException" in after


def test_compose_routes_llm_through_toxiproxy_and_supports_runtime_copy() -> None:
    compose = yaml.safe_load(read("docker-compose.yml"))
    services = compose["services"]

    assert services["api"]["environment"]["LLM_API_BASE"] == "http://toxiproxy:8666/v1"
    assert services["worker"]["environment"]["LLM_API_BASE"] == "http://toxiproxy:8666/v1"
    assert "../../docuask:/app/docuask" in services["api"]["volumes"]
    assert "../../docuask:/app/docuask" in services["worker"]["volumes"]
    assert services["toxiproxy"]["image"].startswith("ghcr.io/shopify/toxiproxy")
    assert "mock-llm:8888" in read("config/toxiproxy.json")


def test_scripts_use_real_toxiproxy_api_and_common_helpers() -> None:
    for script in (LAB_DIR / "scripts").glob("*.sh"):
        text = script.read_text()
        assert "../../../shared/scripts/common.sh" in text
        if "compose()" in text:
            assert "docker compose" in text
            assert "docker-compose" in text
            assert '-f "$LAB_DIR/docker-compose.yml"' in text

    break_script = read("scripts/break.sh")
    reset_script = read("scripts/reset.sh")

    assert "POST" in break_script
    assert "/proxies/mock-llm/toxics" in break_script
    assert "latency" in break_script
    assert "DELETE" in reset_script
    assert "/proxies/mock-llm/toxics/llm-latency" in reset_script


def test_makefile_pins_lab_compose_file() -> None:
    makefile = read("Makefile")

    assert "-f docker-compose.yml" in makefile


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
    assert "MAX_ALLOWED_SECONDS" in load
    assert "bad_status_count" in load
    assert "http_code" in load


def test_runtime_pytests_exist_for_before_and_after_contracts() -> None:
    before_test = read("tests/test_failure_before.py")
    after_test = read("tests/test_resilience_after.py")

    assert "LATENCY_MS" in before_test
    assert "assert elapsed" in before_test
    assert "MAX_ALLOWED_SECONDS" in after_test
    assert "assert response.status_code" in after_test


def test_docs_and_dashboard_describe_timeout_lab() -> None:
    readme = read("README.md")
    architecture = read("architecture.md")
    reflection = read("reflection.md")
    dashboard = json.loads(read("dashboards/grafana-dashboard.json"))

    assert "make break" in readme
    assert "make apply-fix" in readme
    assert "Toxiproxy" in architecture
    assert "connect/read/write/pool" in architecture
    assert "Root Cause" in reflection
    assert "Production Checklist" in reflection
    assert "Before" in reflection
    assert "After" in reflection
    assert "bounded latency" in reflection
    assert dashboard["title"] == "DocuAsk Lab 2 - Timeouts"
