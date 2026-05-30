"""Question-answering routes."""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends

from docuask.api.dependencies.llm import LLMClient, get_llm_client
from docuask.api.dependencies.vector import get_vector_store
from docuask.schemas import QuestionRequest, QuestionResponse
from docuask.vector.store import VectorStore

router = APIRouter(prefix="/questions", tags=["questions"])


@router.post("", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    vector_store: VectorStore = Depends(get_vector_store),
    llm: LLMClient = Depends(get_llm_client),
) -> QuestionResponse:
    """Answer a question using embedding search over document chunks."""
    started = time.perf_counter()
    embeddings = await llm.embed_texts([request.question])
    query_embedding = embeddings[0] if embeddings else []
    matches = await vector_store.search(
        query_embedding,
        limit=5,
        document_id=request.document_id,
    )
    contexts = [match.content for match in matches]
    answer = await llm.answer_question(request.question, contexts)
    return QuestionResponse(
        question=request.question,
        answer=answer,
        sources=contexts,
        latency_ms=(time.perf_counter() - started) * 1000,
    )
