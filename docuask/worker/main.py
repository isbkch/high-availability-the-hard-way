"""Dramatiq worker entrypoint."""

from __future__ import annotations

import sys

from docuask.worker.broker import configure_broker


configure_broker()

from docuask.worker.tasks import process_document  # noqa: E402,F401


def main() -> None:
    """Run the Dramatiq CLI for the DocuAsk worker module."""
    configure_broker()
    from dramatiq.cli import main as dramatiq_main

    if len(sys.argv) == 1:
        sys.argv.append("docuask.worker.tasks")
    dramatiq_main()


if __name__ == "__main__":
    main()
