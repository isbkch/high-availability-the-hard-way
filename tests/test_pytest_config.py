"""Static contract tests for repository pytest configuration."""

from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_pytest_uses_importlib_mode_for_repeated_lab_test_names() -> None:
    config_path = ROOT_DIR / "pytest.ini"
    assert config_path.exists(), "pytest.ini is required for shared lab test collection"

    config = config_path.read_text()

    assert "--import-mode=importlib" in config
