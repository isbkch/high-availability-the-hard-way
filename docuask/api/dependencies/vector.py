"""Vector store dependency helpers."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from docuask.database import get_db
from docuask.vector.store import VectorStore


def get_vector_store(db: AsyncSession = Depends(get_db)) -> VectorStore:
    """Return a vector store bound to the request database session."""
    return VectorStore(db)
