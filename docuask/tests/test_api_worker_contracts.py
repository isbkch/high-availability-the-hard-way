"""Contract tests for the DocuAsk API and worker MVP."""

import asyncio

from docuask.models import Document, DocumentChunk, DocumentStatus


def test_main_app_imports_with_expected_routes():
    """The FastAPI app should expose the Day 1 MVP route surface."""
    from docuask.api.main import app

    routes = {route.path for route in app.routes}

    assert "/health" in routes
    assert "/documents" in routes
    assert "/documents/{document_id}" in routes
    assert "/questions" in routes


def test_vector_store_ranks_stored_chunks_by_embedding_similarity():
    """Vector search should use stored chunk embeddings instead of a fixed sample."""
    from docuask.vector.store import VectorStore, encode_embedding

    class Result:
        def scalars(self):
            return self

        def all(self):
            return [
                DocumentChunk(
                    document_id=1,
                    content="restart postgres primary",
                    chunk_index=0,
                    embedding=encode_embedding([1.0, 0.0]),
                ),
                DocumentChunk(
                    document_id=2,
                    content="rotate api credentials",
                    chunk_index=0,
                    embedding=encode_embedding([0.0, 1.0]),
                ),
            ]

    class Session:
        async def execute(self, _statement):
            return Result()

    matches = asyncio.run(VectorStore(Session()).search([0.9, 0.1], limit=1))

    assert [match.content for match in matches] == ["restart postgres primary"]


def test_worker_process_document_chunks_and_persists_embeddings(monkeypatch):
    """Document processing should transition status and persist embedded chunks."""
    from docuask.worker import tasks

    document = Document(
        id=7,
        title="Runbook",
        content=("alpha " * 900) + ("beta " * 900),
    )
    added_chunks = []

    class Session:
        async def get(self, model, document_id):
            assert model is Document
            assert document_id == 7
            return document

        def add(self, obj):
            added_chunks.append(obj)

        async def execute(self, _statement):
            return None

        async def commit(self):
            return None

        async def rollback(self):
            return None

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

    async def fake_embed_texts(texts):
        return [[float(index), 1.0] for index, _text in enumerate(texts)]

    monkeypatch.setattr(tasks.database, "async_session_maker", lambda: Session())
    monkeypatch.setattr(tasks, "embed_texts", fake_embed_texts)

    asyncio.run(tasks.process_document_async(7))

    assert document.status == DocumentStatus.COMPLETED
    assert document.error_message is None
    assert document.chunk_count == len(added_chunks)
    assert len(added_chunks) > 1
    assert all(chunk.embedding for chunk in added_chunks)
