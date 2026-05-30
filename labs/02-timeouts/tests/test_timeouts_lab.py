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

    assert "httpx.AsyncClient()" in before
    assert "timeout=" not in before
    assert "httpx.Timeout" not in before


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

    break_script = read("scripts/break.sh")
    reset_script = read("scripts/reset.sh")

    assert "POST" in break_script
    assert "/proxies/mock-llm/toxics" in break_script
    assert "latency" in break_script
    assert "DELETE" in reset_script
    assert "/proxies/mock-llm/toxics/llm-latency" in reset_script


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


def test_docs_and_dashboard_describe_timeout_lab() -> None:
    readme = read("README.md")
    architecture = read("architecture.md")
    reflection = read("reflection.md")
    dashboard = json.loads(read("dashboards/grafana-dashboard.json"))

    assert "make break" in readme
    assert "make apply-fix" in readme
    assert "Toxiproxy" in architecture
    assert "connect/read/write/pool" in architecture
    assert "bounded latency" in reflection
    assert dashboard["title"] == "DocuAsk Lab 2 - Timeouts"
