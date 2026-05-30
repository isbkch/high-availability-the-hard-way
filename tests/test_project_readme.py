"""Static contract tests for the project-level README."""

from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_project_readme_covers_day_one_mvp_positioning() -> None:
    readme_path = ROOT_DIR / "README.md"
    assert readme_path.exists(), "README.md is required at the repository root"

    readme = readme_path.read_text()

    required_phrases = [
        "# High Availability The Hard Way",
        "Break it -> Observe it -> Understand it -> Fix it -> Prove it",
        "DocuAsk",
        "| 1 | Baseline App |",
        "| 2 | Timeouts |",
        "| 3 | Retries + Jitter |",
        "YouTube is the acquisition engine",
        "The GitHub repository is the source of truth",
        "The companion site organizes the journey",
        "make up",
        "make smoke-test",
        "make break",
        "make apply-fix",
        "make load-test",
        "Prometheus",
        "Grafana",
    ]

    for phrase in required_phrases:
        assert phrase in readme
