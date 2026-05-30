"""OpenTelemetry observability setup for the API."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, Request
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except ImportError:  # pragma: no cover - optional in lightweight local envs
    FastAPIInstrumentor = None

try:
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
except ImportError:  # pragma: no cover - optional in lightweight local envs
    HTTPXClientInstrumentor = None


_httpx_instrumented = False


def instrument_app(app: FastAPI) -> None:
    """Instrument FastAPI and httpx once for local lab observability."""
    global _httpx_instrumented

    provider = trace.get_tracer_provider()
    if not isinstance(provider, TracerProvider):
        trace.set_tracer_provider(
            TracerProvider(resource=Resource.create({"service.name": "docuask-api"}))
        )

    if FastAPIInstrumentor is not None:
        FastAPIInstrumentor.instrument_app(app)

    if HTTPXClientInstrumentor is not None and not _httpx_instrumented:
        HTTPXClientInstrumentor().instrument()
        _httpx_instrumented = True


async def request_middleware(request: Request, call_next: Callable[..., Any]) -> Any:
    """Add a small custom span around each request."""
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("http.request") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        response = await call_next(request)
        span.set_attribute("http.status_code", response.status_code)
        return response
