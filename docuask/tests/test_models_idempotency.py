"""Unit contract for the shared IdempotencyKey model."""

from __future__ import annotations

from docuask.models import IdempotencyKey


def test_idempotency_key_table_and_columns() -> None:
    assert IdempotencyKey.__tablename__ == "idempotency_keys"
    columns = IdempotencyKey.__table__.columns
    assert "key" in columns
    assert columns["key"].primary_key
    assert "request_hash" in columns
    assert columns["request_hash"].nullable is False
    assert "document_id" in columns
    assert columns["document_id"].nullable is True
    assert "created_at" in columns
