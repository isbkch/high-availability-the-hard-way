"""Pydantic schemas for API serialization."""

from datetime import datetime

from pydantic import BaseModel, Field

from docuask.models import DocumentStatus


class DocumentCreate(BaseModel):
    """Request body for creating a document."""

    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)


class DocumentResponse(BaseModel):
    """Response body for a document."""

    id: int
    title: str
    status: DocumentStatus
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    chunk_count: int = 0

    model_config = {"from_attributes": True}


class QuestionRequest(BaseModel):
    """Request body for asking a question."""

    question: str = Field(..., min_length=1, max_length=1000)
    document_id: int | None = None


class QuestionResponse(BaseModel):
    """Response body for a question answer."""

    question: str
    answer: str
    sources: list[str] = Field(default_factory=list)
    latency_ms: float


class HealthResponse(BaseModel):
    """Response body for health checks."""

    status: str
    database: str
    redis: str
    llm: str
