"""Smoke checks for DocuAsk core modules."""

from docuask.config import Settings
from docuask.models import Document, DocumentChunk, DocumentStatus
from docuask.schemas import DocumentCreate, QuestionRequest


def test_settings_generate_async_database_url_from_environment(monkeypatch):
    """Settings should honor env vars when building the async database URL."""
    monkeypatch.setenv("POSTGRES_USER", "alice")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("POSTGRES_DB", "knowledge")
    monkeypatch.setenv("POSTGRES_HOST", "db")
    monkeypatch.setenv("POSTGRES_PORT", "6543")

    settings = Settings()

    assert (
        settings.generate_database_url()
        == "postgresql+asyncpg://alice:secret@db:6543/knowledge"
    )


def test_models_and_schemas_import_with_expected_defaults():
    """Core models and schemas should be importable with intended defaults."""
    document = Document(title="Runbook", content="Failover steps")
    chunk = DocumentChunk(document_id=1, content="Failover", chunk_index=0)
    create_request = DocumentCreate(title="Runbook", content="Failover steps")
    question_request = QuestionRequest(question="What should I do?")

    assert document.status == DocumentStatus.PENDING
    assert document.chunk_count == 0
    assert chunk.document_id == 1
    assert create_request.title == "Runbook"
    assert question_request.document_id is None


def test_database_exposes_async_session_maker_for_workers():
    """Workers should be able to import the planned session factory name."""
    from docuask import database

    assert callable(database.async_session_maker)


def test_document_status_enum_uses_lowercase_storage_values():
    """Database enum labels should match the public API status values."""
    status_type = Document.__table__.c.status.type

    assert status_type.enums == ["pending", "processing", "completed", "failed"]
