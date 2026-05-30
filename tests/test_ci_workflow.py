"""Static contract tests for GitHub Actions lab checks."""

from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_github_actions_workflow_runs_static_lab_contracts() -> None:
    workflow_path = ROOT_DIR / ".github/workflows/test-labs.yml"
    assert workflow_path.exists(), "missing .github/workflows/test-labs.yml"

    workflow = workflow_path.read_text()

    required_snippets = [
        "name: Test labs",
        "python-version: '3.11'",
        "pyyaml",
        "python3 -m pytest docuask/tests tests labs/01-baseline-app/tests labs/02-timeouts/tests labs/03-retries-jitter/tests -q",
        "bash -n shared/scripts/*.sh labs/01-baseline-app/scripts/*.sh labs/02-timeouts/scripts/*.sh labs/03-retries-jitter/scripts/*.sh",
        "docker compose -f shared/docker-compose.yml config --quiet",
        "docker compose -f labs/01-baseline-app/docker-compose.yml config --quiet",
        "docker compose -f labs/02-timeouts/docker-compose.yml config --quiet",
        "docker compose -f labs/03-retries-jitter/docker-compose.yml config --quiet",
        "git diff --check",
    ]

    for snippet in required_snippets:
        assert snippet in workflow
