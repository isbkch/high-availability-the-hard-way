"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from docuask.api.middleware.observability import instrument_app
from docuask.api.routes import documents, health, questions
from docuask.database import close_db, init_db

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Initialize and close application resources."""
    await init_db()
    try:
        yield
    finally:
        await close_db()


app = FastAPI(title="DocuAsk", version="0.1.0", lifespan=lifespan)
app.include_router(health.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(questions.router, prefix="/api")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
instrument_app(app)


@app.get("/")
async def root() -> FileResponse:
    """Serve the browser demo used by the labs and launch recording."""
    return FileResponse(STATIC_DIR / "index.html")
