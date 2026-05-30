"""Dramatiq worker entrypoint."""

from __future__ import annotations

from docuask.config import get_settings

try:
    import dramatiq
    from dramatiq.brokers.redis import RedisBroker
except ImportError:  # pragma: no cover - allows import smoke tests without extras
    dramatiq = None
    RedisBroker = None


def configure_broker() -> None:
    """Configure the Redis broker for Dramatiq."""
    if dramatiq is None or RedisBroker is None:
        return
    broker = RedisBroker(url=get_settings().redis_url)
    dramatiq.set_broker(broker)


configure_broker()

from docuask.worker.tasks import process_document  # noqa: E402,F401
