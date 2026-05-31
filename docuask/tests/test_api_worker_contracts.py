"""Contract tests for the DocuAsk API and worker MVP."""

import asyncio
import importlib
import sys
import types
from pathlib import Path

from docuask.models import Document, DocumentChunk, DocumentStatus


def test_main_app_imports_with_expected_routes():
    """The FastAPI app should expose the Day 1 MVP route surface."""
    from docuask.api.main import app

    routes = {route.path for route in app.routes}

    assert "/" in routes
    assert "/api/health" in routes
    assert "/api/documents" in routes
    assert "/api/documents/{document_id}" in routes
    assert "/api/questions" in routes


def test_root_serves_docuask_demo_ui():
    """The root page should be a browser demo for launch recordings."""
    from fastapi.testclient import TestClient

    from docuask.api.main import app

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DocuAsk Reliability Lab" in response.text
    assert 'id="document-form"' in response.text
    assert 'id="question-form"' in response.text


def test_demo_static_assets_reference_public_api_contracts():
    """The browser demo should call the same API routes used in the labs."""
    root = Path(__file__).resolve().parents[1]
    static_dir = root / "api" / "static"

    index = (static_dir / "index.html").read_text()
    script = (static_dir / "app.js").read_text()
    styles = (static_dir / "styles.css").read_text()

    assert 'href="/static/styles.css"' in index
    assert 'src="/static/app.js"' in index
    assert '"/api/health"' in script
    assert '"/api/documents"' in script
    assert '"/api/questions"' in script
    assert "DocuAsk" in styles


def test_health_route_returns_lab_contract_status_values(monkeypatch):
    """Smoke scripts expect healthy/unhealthy/degraded labels, not ok/error."""
    from docuask.api.routes import health as health_module

    class Database:
        async def execute(self, _statement):
            return None

    class RedisClient:
        async def ping(self):
            return True

        async def aclose(self):
            return None

    class LLM:
        async def health(self):
            return "healthy"

    monkeypatch.setattr(health_module, "get_redis_client", lambda: RedisClient())

    response = asyncio.run(health_module.health(db=Database(), llm=LLM()))

    assert response.status == "healthy"
    assert response.database == "healthy"
    assert response.redis == "healthy"
    assert response.llm == "healthy"


def test_redis_dependency_uses_short_socket_timeouts():
    """Dependency checks should fail fast when Redis is unreachable."""
    from docuask.api.dependencies.redis import get_redis_client

    client = get_redis_client()
    kwargs = client.connection_pool.connection_kwargs

    assert kwargs["socket_connect_timeout"] <= 1.0
    assert kwargs["socket_timeout"] <= 1.0


def test_worker_tasks_configures_redis_broker_before_actor_import(monkeypatch):
    """Dramatiq actors should bind to the configured Docker Redis broker."""
    for module_name in [
        "docuask.worker.tasks",
        "docuask.worker.main",
        "docuask.worker.broker",
        "dramatiq",
        "dramatiq.brokers",
        "dramatiq.brokers.redis",
        "dramatiq.middleware",
    ]:
        sys.modules.pop(module_name, None)

    fake_dramatiq = types.ModuleType("dramatiq")
    fake_dramatiq.broker_configured = False
    fake_dramatiq.actor_saw_configured_broker = False

    def set_broker(_broker):
        fake_dramatiq.broker_configured = True

    def actor(fn):
        fake_dramatiq.actor_saw_configured_broker = fake_dramatiq.broker_configured
        return types.SimpleNamespace(fn=fn, send=lambda *args, **kwargs: None)

    fake_dramatiq.set_broker = set_broker
    fake_dramatiq.actor = actor

    redis_module = types.ModuleType("dramatiq.brokers.redis")

    class RedisBroker:
        def __init__(self, url):
            self.url = url
            self.middleware = ["prometheus", ("time_limit", 300_000)]

        def add_middleware(self, middleware):
            self.middleware.append(middleware)

    redis_module.RedisBroker = RedisBroker

    middleware_module = types.ModuleType("dramatiq.middleware")
    middleware_module.Prometheus = lambda: "prometheus"
    middleware_module.TimeLimit = lambda time_limit: ("time_limit", time_limit)

    monkeypatch.setitem(sys.modules, "dramatiq", fake_dramatiq)
    monkeypatch.setitem(sys.modules, "dramatiq.brokers", types.ModuleType("dramatiq.brokers"))
    monkeypatch.setitem(sys.modules, "dramatiq.brokers.redis", redis_module)
    monkeypatch.setitem(sys.modules, "dramatiq.middleware", middleware_module)

    importlib.import_module("docuask.worker.tasks")

    assert fake_dramatiq.broker_configured is True
    assert fake_dramatiq.actor_saw_configured_broker is True
    broker = sys.modules["docuask.worker.broker"]._broker
    assert broker.middleware == ["prometheus", ("time_limit", 300_000)]


def test_requirements_pin_available_dramatiq_version():
    """Docker builds should not depend on a non-existent Dramatiq release."""
    root = Path(__file__).resolve().parents[2]

    for path in [
        root / "docuask" / "api" / "requirements.txt",
        root / "docuask" / "worker" / "requirements.txt",
    ]:
        assert "dramatiq==1.15.0" in path.read_text()


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
