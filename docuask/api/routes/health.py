"""Health routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from docuask.api.dependencies.llm import LLMClient, get_llm_client
from docuask.api.dependencies.redis import get_redis_client
from docuask.database import get_db
from docuask.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(
    db: AsyncSession = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
) -> HealthResponse:
    """Report database, Redis, and LLM dependency status."""
    database_status = "ok"
    redis_status = "ok"

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"

    redis_client = get_redis_client()
    try:
        await redis_client.ping()
    except Exception:
        redis_status = "error"
    finally:
        await redis_client.aclose()

    llm_status = await llm.health()
    status = (
        "ok"
        if database_status == redis_status == llm_status == "ok"
        else "degraded"
    )
    return HealthResponse(
        status=status,
        database=database_status,
        redis=redis_status,
        llm=llm_status,
    )
