"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

from docuask.api.middleware.telemetry import configure_telemetry
from docuask.api.routes import documents, health, questions
from docuask.database import close_db, init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and close application resources."""
    await init_db()
    try:
        yield
    finally:
        await close_db()


app = FastAPI(title="DocuAsk", version="0.1.0", lifespan=lifespan)
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(questions.router)
configure_telemetry(app)
