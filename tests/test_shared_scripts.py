"""Static contract tests for shared shell helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_common_helpers_do_not_overwrite_callers_script_dir() -> None:
    result = subprocess.run(
        [
            "bash",
            "-c",
            (
                "set -euo pipefail; "
                "SCRIPT_DIR=/tmp/caller; "
                "source shared/scripts/common.sh; "
                'test "$SCRIPT_DIR" = /tmp/caller'
            ),
        ],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
