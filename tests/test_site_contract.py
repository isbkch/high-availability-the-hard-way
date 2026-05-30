"""Static contract tests for the minimal Astro companion site."""

from __future__ import annotations

import json
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_companion_site_scaffold_matches_day_one_scope() -> None:
    site_dir = ROOT_DIR / "site"
    package_json = site_dir / "package.json"
    astro_config = site_dir / "astro.config.mjs"
    index_page = site_dir / "src/pages/index.astro"
    layout = site_dir / "src/layouts/Layout.astro"
    system_map = site_dir / "public/system-map.svg"

    for path in (package_json, astro_config, index_page, layout, system_map):
        assert path.exists(), f"missing {path.relative_to(ROOT_DIR)}"

    package = json.loads(package_json.read_text())
    assert package["scripts"]["dev"] == "astro dev"
    assert package["scripts"]["build"] == "astro build"
    assert "astro" in package["dependencies"]

    page = index_page.read_text()
    required_phrases = [
        "High Availability The Hard Way",
        "Break it -> Observe it -> Understand it -> Fix it -> Prove it",
        "DocuAsk",
        "Baseline App",
        "Timeouts",
        "Retries + Jitter",
        "GitHub repository is the source of truth",
        "YouTube is the acquisition engine",
        "Companion site organizes the journey",
        "/system-map.svg",
    ]

    for phrase in required_phrases:
        assert phrase in page
