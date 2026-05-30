# DocuAsk Architecture

DocuAsk is a small document Q&A system used to practice reliability engineering on a real multi-service app.

## Components

### API Service

The FastAPI service exposes the current DocuAsk API contract:

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Return API dependency health using `healthy`, `degraded`, and `unhealthy` labels |
| POST | `/api/documents` | Create a document and enqueue background processing |
| GET | `/api/documents` | List documents newest first |
| GET | `/api/documents/{document_id}` | Fetch one document |
| POST | `/api/questions` | Embed the question, search document chunks, and ask the LLM |

In curl-style shorthand, those routes are `GET /api/health`, `POST /api/documents`, `GET /api/documents`, `GET /api/documents/{document_id}`, and `POST /api/questions`.

The API starts with `uvicorn docuask.api.main:app --host 0.0.0.0 --port 8080`.

### Worker Service

The worker uses Dramatiq and Redis. In this lab it starts through the project entrypoint:

```bash
python -m docuask.worker.main docuask.worker.tasks --processes 2 --threads 2
```

The worker receives document IDs, chunks the content, asks the mock LLM for embeddings, and stores chunks for later question answering.

### PostgreSQL + pgvector

PostgreSQL stores documents and chunks. The `pgvector/pgvector:pg16` image provides vector support for embedding search.

### Redis

Redis is the Dramatiq broker. The API enqueues jobs into Redis, and the worker consumes them.

### Mock LLM

The lab includes a small OpenAI-compatible mock service for:

- `GET /v1/models`
- `POST /v1/embeddings`
- `POST /v1/chat/completions`

It is deterministic so the baseline works without external credentials.

### Observability

Prometheus and Grafana run in the same Compose project. Prometheus targets services by Compose service name so container networking matches later failure-injection labs.

## Data Flow

Document upload:

```text
User -> API -> PostgreSQL document row -> Redis queue -> Worker -> Mock LLM embeddings -> PostgreSQL chunks
```

Question answering:

```text
User -> API -> Mock LLM embedding -> PostgreSQL vector search -> Mock LLM chat completion -> API response
```

Health check:

```text
User -> API -> PostgreSQL ping + Redis ping + Mock LLM /v1/models
```

## Baseline Failure Surfaces

| Boundary | Later risk |
| --- | --- |
| API to mock LLM | Missing timeouts, retries, and circuit breakers |
| API to Redis | Queue enqueue failures |
| Worker to Redis | Worker stalls or disconnects |
| Worker to PostgreSQL | Failed status updates and partial processing |
| Health checks | Shallow dependency reporting |
