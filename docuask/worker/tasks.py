"""Dramatiq tasks for document processing."""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import delete

from docuask import database
from docuask.api.dependencies.llm import embed_texts
from docuask.models import Document, DocumentChunk, DocumentStatus
from docuask.vector.store import encode_embedding
from docuask.worker.broker import actor

logger = logging.getLogger(__name__)

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
