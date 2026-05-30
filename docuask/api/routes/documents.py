"""Document routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from docuask.database import get_db
from docuask.models import Document
from docuask.schemas import DocumentCreate, DocumentResponse
from docuask.worker.tasks import process_document

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    request: DocumentCreate,
    db: AsyncSession = Depends(get_db),
) -> Document:
    """Create a document and enqueue it for background processing."""
    document = Document(title=request.title, content=request.content)
    db.add(document)
    await db.commit()
    await db.refresh(document)
    process_document.send(document.id)
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
