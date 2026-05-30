"""Dramatiq tasks for document processing with embedding backoff and jitter."""

from __future__ import annotations

import asyncio
import logging
import random

import httpx
from sqlalchemy import delete

from docuask import database
from docuask.config import get_settings
from docuask.models import Document, DocumentChunk, DocumentStatus
from docuask.vector.store import encode_embedding
from docuask.worker.broker import actor

logger = logging.getLogger(__name__)

MAX_EMBEDDING_RETRY_ATTEMPTS = 4
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
EMBEDDING_TIMEOUT = httpx.Timeout(connect=1.0, read=2.0, write=1.0, pool=0.5)
EMBEDDING_RETRY_BASE_DELAY_SECONDS = 0.15
EMBEDDING_RETRY_MAX_DELAY_SECONDS = 1.2
EMBEDDING_RETRY_JITTER_SECONDS = 0.25


def embedding_retry_delay(attempt: int) -> float:
    """Return exponential backoff plus jitter for the completed attempt."""
    backoff = min(
        EMBEDDING_RETRY_MAX_DELAY_SECONDS,
        EMBEDDING_RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1)),
    )
    return backoff + random.uniform(0.0, EMBEDDING_RETRY_JITTER_SECONDS)


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Call the LLM embeddings endpoint with a visible retry budget."""
    settings = get_settings()
    payload = {"model": "text-embedding-3-small", "input": texts}
    last_response: httpx.Response | None = None
    last_error: Exception | None = None
    async with httpx.AsyncClient(timeout=EMBEDDING_TIMEOUT) as client:
        for attempt in range(1, MAX_EMBEDDING_RETRY_ATTEMPTS + 1):
            try:
                response = await client.post(
                    f"{settings.llm_api_base.rstrip('/')}/embeddings",
                    headers={
                        "Authorization": f"Bearer {settings.llm_api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
                if response.status_code not in RETRYABLE_STATUS_CODES:
                    response.raise_for_status()
                    data = response.json()
                    return [item["embedding"] for item in data.get("data", [])]
                last_response = response
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc

            if attempt == MAX_EMBEDDING_RETRY_ATTEMPTS:
                break
            delay = embedding_retry_delay(attempt)
            await asyncio.sleep(delay)

    if last_response is not None:
        last_response.raise_for_status()
    raise RuntimeError(
        f"LLM embeddings failed after retry budget of {MAX_EMBEDDING_RETRY_ATTEMPTS} attempts"
    ) from last_error


def chunk_text(text: str, *, chunk_size: int = 3000, overlap: int = 200) -> list[str]:
    """Split text into overlapping chunks."""
    cleaned = text.strip()
    if not cleaned:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunks.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(end - overlap, start + 1)
    return chunks


async def process_document_async(document_id: int) -> None:
    """Process one document into embedded chunks."""
    async with database.async_session_maker() as db:
        document = await db.get(Document, document_id)
        if document is None:
            logger.warning("Document %s not found", document_id)
            return

        try:
            document.status = DocumentStatus.PROCESSING
            document.error_message = None
            await db.commit()

            chunks = chunk_text(document.content)
            embeddings = await embed_texts(chunks) if chunks else []
            await db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == document.id)
            )
            for index, chunk in enumerate(chunks):
                embedding = embeddings[index] if index < len(embeddings) else []
                db.add(
                    DocumentChunk(
                        document_id=document.id,
                        content=chunk,
                        chunk_index=index,
                        embedding=encode_embedding(embedding),
                    )
                )

            document.status = DocumentStatus.COMPLETED
            document.error_message = None
            document.chunk_count = len(chunks)
            await db.commit()
        except Exception as exc:
            await db.rollback()
            document.status = DocumentStatus.FAILED
            document.error_message = str(exc)[:1000]
            await db.commit()
            raise


@actor
def process_document(document_id: int) -> None:
    """Dramatiq actor wrapper for document processing."""
    asyncio.run(process_document_async(document_id))
