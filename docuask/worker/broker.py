"""Dramatiq broker configuration shared by API and worker imports."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from docuask.config import get_settings

try:
    import dramatiq
    from dramatiq.brokers.redis import RedisBroker
    from dramatiq.middleware import Prometheus, TimeLimit
except ImportError:  # pragma: no cover - allows lightweight local tests
    dramatiq = None
    RedisBroker = None
    Prometheus = None
    TimeLimit = None


_broker: Any | None = None


class InlineActor:
    """Small fallback with the actor API used by local tests."""

    def __init__(self, fn: Callable[..., Any]):
        self.fn = fn

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)

    def send(self, *args: Any, **kwargs: Any) -> Any:
        return self.fn(*args, **kwargs)


def configure_broker() -> Any | None:
    """Configure Dramatiq to use the Redis URL from application settings."""
    global _broker

    if dramatiq is None or RedisBroker is None:
        return None

    if _broker is None:
        broker = RedisBroker(url=get_settings().redis_url)
        if Prometheus is not None:
            broker.add_middleware(Prometheus())
        if TimeLimit is not None:
            broker.add_middleware(TimeLimit(time_limit=300_000))
        dramatiq.set_broker(broker)
        _broker = broker

    return _broker


def actor(fn: Callable[..., Any]) -> Any:
    """Create a Dramatiq actor after broker configuration."""
    if dramatiq is None:
        return InlineActor(fn)

    configure_broker()
    return dramatiq.actor(fn)
