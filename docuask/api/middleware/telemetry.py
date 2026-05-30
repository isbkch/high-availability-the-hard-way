"""OpenTelemetry setup for the API."""

from __future__ import annotations

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:  # pragma: no cover - depends on optional runtime package
    FastAPIInstrumentor = None

try:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
except ImportError:  # pragma: no cover - depends on optional runtime package
    HTTPXClientInstrumentor = None


def configure_telemetry(app: FastAPI) -> None:
    """Configure OpenTelemetry instrumentation if it has not already run."""
    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        trace.set_tracer_provider(
            TracerProvider(resource=Resource.create({"service.name": "docuask-api"}))
        )
    if FastAPIInstrumentor is not None:
        FastAPIInstrumentor.instrument_app(app)
    if HTTPXClientInstrumentor is not None:
        HTTPXClientInstrumentor().instrument()
