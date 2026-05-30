# Architecture

Lab 2 uses the same DocuAsk service shape as Lab 1 and inserts Toxiproxy between DocuAsk and the mock LLM.

```text
browser/curl
    |
    v
DocuAsk API :8080
    |
    +--> PostgreSQL/pgvector :5432
    +--> Redis :6379
    +--> Toxiproxy :8666
              |
              v
          mock-llm :8888

DocuAsk worker
    |
    +--> Redis
    +--> PostgreSQL/pgvector
    +--> Toxiproxy :8666 -> mock-llm :8888
```

The API and worker both use:

```text
LLM_API_BASE=http://toxiproxy:8666/v1
```

Toxiproxy is configured with a `mock-llm` proxy whose upstream is `mock-llm:8888`. The latency failure is created with `POST /proxies/mock-llm/toxics` and removed with `DELETE /proxies/mock-llm/toxics/llm-latency`.

## Before

The before implementation uses `httpx.AsyncClient()` for embeddings, chat completions, and LLM health checks. There is no explicit application timeout budget on the LLM dependency path.

## After

The after implementation uses one explicit `httpx.Timeout` for normal LLM calls and a shorter health-check timeout:

```text
connect/read/write/pool
```

The important behavior is bounded latency: when Toxiproxy adds more latency than the read budget allows, the API and worker fail fast instead of waiting behind the dependency.

## API Routes

- `GET /api/health`
- `POST /api/documents`
- `GET /api/documents`
- `GET /api/documents/{document_id}`
- `POST /api/questions`
