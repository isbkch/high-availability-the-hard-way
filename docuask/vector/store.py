"""Simple database-backed vector storage and search."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from docuask.models import DocumentChunk


def encode_embedding(values: Iterable[float]) -> bytes:
    """Encode a float embedding for storage in the current LargeBinary column."""
    vector = [float(value) for value in values]
    return struct.pack(f"!{len(vector)}f", *vector)


def decode_embedding(payload: bytes | None) -> list[float]:
    """Decode a stored embedding payload."""
    if not payload:
        return []
    if len(payload) % 4 != 0:
        return []
    return list(struct.unpack(f"!{len(payload) // 4}f", payload))


@dataclass(frozen=True)
class VectorMatch:
    """A search result from the chunk store."""

    chunk_id: int | None
    document_id: int
    content: str
    score: float


class VectorStore:
    """MVP vector store over persisted document chunks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(
        self,
        query_embedding: list[float],
        *,
        limit: int = 5,
        document_id: int | None = None,
    ) -> list[VectorMatch]:
        """Return chunks ranked by cosine similarity."""
        statement = select(DocumentChunk)
        if document_id is not None:
            statement = statement.where(DocumentChunk.document_id == document_id)
        result = await self.db.execute(statement)
        chunks = result.scalars().all()

        matches: list[VectorMatch] = []
        for chunk in chunks:
            embedding = decode_embedding(chunk.embedding)
            if not embedding:
                # Older chunks may not have embeddings yet; keep them searchable
                # behind embedded chunks so the API can still answer MVP demos.
                score = 0.0
            else:
                score = cosine_similarity(query_embedding, embedding)
            matches.append(
                VectorMatch(
                    chunk_id=chunk.id,
                    document_id=chunk.document_id,
                    content=chunk.content,
                    score=score,
                )
            )

        matches.sort(key=lambda match: match.score, reverse=True)
        return matches[:limit]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity for two embeddings."""
    dimensions = min(len(left), len(right))
    if dimensions == 0:
        return 0.0
    left_values = left[:dimensions]
    right_values = right[:dimensions]
    dot = sum(a * b for a, b in zip(left_values, right_values, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left_values))
    right_norm = math.sqrt(sum(value * value for value in right_values))
    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0
    return dot / (left_norm * right_norm)
