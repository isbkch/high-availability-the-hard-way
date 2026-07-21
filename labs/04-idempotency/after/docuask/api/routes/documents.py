"""Document routes with idempotent creation."""

from __future__ import annotations

import asyncio
import hashlib

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from docuask.database import get_db
from docuask.models import Document, DocumentStatus, IdempotencyKey
from docuask.schemas import DocumentCreate, DocumentResponse
from docuask.worker.tasks import process_document

router = APIRouter(prefix="/documents", tags=["documents"])

REPLAY_POLL_ATTEMPTS = 20
REPLAY_POLL_DELAY_SECONDS = 0.1


def request_fingerprint(request: DocumentCreate) -> str:
    """Return a stable sha256 of the request body for replay validation."""
    raw = f"{request.title}\n{request.content}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


async def _create_and_enqueue(db: AsyncSession, request: DocumentCreate) -> Document:
    """Create a document row and enqueue background processing."""
    document = Document(title=request.title, content=request.content)
    db.add(document)
    await db.commit()
    await db.refresh(document)
    try:
        process_document.send(document.id)
    except Exception as exc:
        document.status = DocumentStatus.FAILED
        document.error_message = f"Failed to enqueue document: {exc}"[:1000]
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Document was saved but could not be queued for processing",
        ) from exc
    return document


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    request: DocumentCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> Document:
    """Create a document, deduplicating retries that share an Idempotency-Key."""
    if not idempotency_key:
        # No key supplied: preserve legacy create-every-time behavior.
        return await _create_and_enqueue(db, request)

    fingerprint = request_fingerprint(request)

    # Reserve the key first. The unique primary key serializes concurrent retries.
    reserve = (
        pg_insert(IdempotencyKey)
        .values(key=idempotency_key, request_hash=fingerprint)
        .on_conflict_do_nothing(index_elements=["key"])
        .returning(IdempotencyKey.key)
    )
    reserved = (await db.execute(reserve)).scalar_one_or_none()

    if reserved is not None:
        # We won the reservation: create the resource exactly once.
        document = Document(title=request.title, content=request.content)
        db.add(document)
        await db.flush()
        await db.execute(
            update(IdempotencyKey)
            .where(IdempotencyKey.key == idempotency_key)
            .values(document_id=document.id)
        )
        await db.commit()
        await db.refresh(document)
        try:
            process_document.send(document.id)
        except Exception as exc:
            document.status = DocumentStatus.FAILED
            document.error_message = f"Failed to enqueue document: {exc}"[:1000]
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document was saved but could not be queued for processing",
            ) from exc
        return document

    # Lost the reservation: a prior request already owns this key.
    await db.rollback()
    existing = await db.get(IdempotencyKey, idempotency_key)
    if existing is None:
        return await _create_and_enqueue(db, request)

    if existing.request_hash != fingerprint:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key was reused with a different request body",
        )

    # Same key, same body: wait briefly for the winner to link its document, then replay.
    for _ in range(REPLAY_POLL_ATTEMPTS):
        if existing.document_id is not None:
            break
        await asyncio.sleep(REPLAY_POLL_DELAY_SECONDS)
        await db.refresh(existing)

    if existing.document_id is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotent request is still in progress; retry shortly",
        )

    document = await db.get(Document, existing.document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    response.headers["Idempotent-Replay"] = "true"
    response.status_code = status.HTTP_200_OK
    return document


@router.get("", response_model=list[DocumentResponse])
async def list_documents(db: AsyncSession = Depends(get_db)) -> list[Document]:
    """List documents in newest-first order."""
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db),
) -> Document:
    """Fetch a single document."""
    document = await db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document
