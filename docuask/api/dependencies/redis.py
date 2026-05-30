"""Redis dependency helpers."""

from __future__ import annotations

from redis.asyncio import Redis

from docuask.config import get_settings


def get_redis_client() -> Redis:
    """Return a lazily-created Redis client."""
    return Redis.from_url(
        get_settings().redis_url,
        socket_connect_timeout=1.0,
        socket_timeout=1.0,
        health_check_interval=30,
    )
