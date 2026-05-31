"""Static contract tests for Lab 1 baseline application assets."""

from __future__ import annotations

import json
from pathlib import Path

import yaml


LAB_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = LAB_DIR.parents[1]


def test_compose_uses_current_docuask_contract() -> None:
    compose = yaml.safe_load((LAB_DIR / "docker-compose.yml").read_text())

    assert "version" not in compose
    services = compose["services"]
    assert services["api"]["ports"] == ["8080:8080"]
    assert services["api"]["environment"]["LLM_API_BASE"] == "http://mock-llm:8888/v1"
    assert services["worker"]["command"] == [
        "python",
        "-m",
        "docuask.worker.main",
        "docuask.worker.tasks",
        "--processes",
        "2",
        "--threads",
        "2",
    ]
    assert "healthcheck" in services["worker"]
    assert services["mock-llm"]["image"] == "python:3.11-slim"
    assert services["mock-llm"]["command"] == ["python", "/app/server.py"]


def test_compose_provisions_lab_observability_by_service_name() -> None:
    compose = yaml.safe_load((LAB_DIR / "docker-compose.yml").read_text())

    prometheus_volumes = compose["services"]["prometheus"]["volumes"]
    grafana_volumes = compose["services"]["grafana"]["volumes"]

    assert "./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro" in prometheus_volumes
    assert "./dashboards:/var/lib/grafana/dashboards:ro" in grafana_volumes

    prometheus_config = yaml.safe_load(
        (LAB_DIR / "prometheus" / "prometheus.yml").read_text()
    )
    targets = {
        target
        for scrape_config in prometheus_config["scrape_configs"]
        for static_config in scrape_config["static_configs"]
        for target in static_config["targets"]
    }
    assert {
        "http://api:8080/api/health",
        "http://mock-llm:8888/v1/models",
        "postgres:5432",
        "redis:6379",
    }.issubset(targets)


def test_scripts_source_common_with_lab_relative_path() -> None:
    for script in (LAB_DIR / "scripts").glob("*.sh"):
        text = script.read_text()
        assert "../../../shared/scripts/common.sh" in text
        if "compose()" in text:
            assert "docker compose" in text
            assert "docker-compose" in text
            assert '-f "$LAB_DIR/docker-compose.yml"' in text


def test_makefile_pins_lab_compose_file() -> None:
    makefile = (LAB_DIR / "Makefile").read_text()

    assert "-f docker-compose.yml" in makefile


def test_startup_and_smoke_test_prove_worker_processing() -> None:
    up_script = (LAB_DIR / "scripts" / "up.sh").read_text()
    smoke_script = (LAB_DIR / "scripts" / "smoke-test.sh").read_text()

    assert "worker container is running" in up_script
    assert 'DOC_STATUS" != "completed"' in smoke_script
    assert "document_id" in smoke_script
    assert "sources" in smoke_script


def test_docs_describe_real_api_routes_and_health_labels() -> None:
    readme = (LAB_DIR / "README.md").read_text()
    architecture = (LAB_DIR / "architecture.md").read_text()

    for route in (
        "GET /api/health",
        "POST /api/documents",
        "GET /api/documents",
        "GET /api/documents/{document_id}",
        "POST /api/questions",
    ):
        assert route in architecture
    assert "healthy" in readme
    assert "degraded" in readme
    assert "unhealthy" in readme


def test_dashboard_and_dockerfiles_are_valid_lab_assets() -> None:
    dashboard = json.loads((LAB_DIR / "dashboards" / "grafana-dashboard.json").read_text())
    assert dashboard["title"] == "DocuAsk Lab 1 - Baseline"

    api_dockerfile = (ROOT_DIR / "Dockerfile.api").read_text()
    worker_dockerfile = (ROOT_DIR / "Dockerfile.worker").read_text()

    assert "uvicorn" in api_dockerfile
    assert "docuask.api.main:app" in api_dockerfile
    assert "uv pip install --system --no-cache" in api_dockerfile
    assert "uv pip install --system --no-cache" in worker_dockerfile
    assert "RUN pip install" not in api_dockerfile
    assert "RUN pip install" not in worker_dockerfile
    assert 'CMD ["python", "-m", "docuask.worker.main"' in worker_dockerfile
