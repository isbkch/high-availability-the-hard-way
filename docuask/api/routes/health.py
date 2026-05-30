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
    database_status = "healthy"
    redis_status = "healthy"

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        database_status = "unhealthy"

    redis_client = get_redis_client()
    try:
        await redis_client.ping()
    except Exception:
        redis_status = "unhealthy"
    finally:
        await redis_client.aclose()

    llm_status = await llm.health()
    if database_status == redis_status == llm_status == "healthy":
        status = "healthy"
    elif database_status == "unhealthy" or redis_status == "unhealthy":
        status = "unhealthy"
    else:
        status = "degraded"
    return HealthResponse(
        status=status,
        database=database_status,
        redis=redis_status,
        llm=llm_status,
    )
