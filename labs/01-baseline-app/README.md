# Lab 1: Baseline Application

## Purpose

This lab starts the DocuAsk application without injecting a failure. The goal is to learn the moving parts, verify the real API contract, and capture the baseline behavior that later labs will break and harden.

## What You Will Learn

- How the API, worker, PostgreSQL, Redis, and mock LLM fit together.
- How to start, stop, reset, and inspect the local stack.
- What the current healthy, degraded, and unhealthy states look like.
- Which service boundaries become reliability risks in later labs.

## Services

| Service | Port | Purpose |
| --- | ---: | --- |
| API | 8080 | FastAPI DocuAsk API under `/api` |
| PostgreSQL + pgvector | 5432 | Documents, chunks, and embeddings |
| Redis | 6379 | Dramatiq broker |
| Worker | internal | Background document chunking and embedding |
| Mock LLM | 8888 | OpenAI-compatible `/v1` test double |
| Prometheus | 9090 | Metrics and probe collection |
| Grafana | 3001 | Baseline dashboard |

## Start

```bash
make up
```

The API is available at `http://localhost:8080`. Grafana is available at `http://localhost:3001` with `admin` / `admin`.

## Smoke Test

```bash
make smoke-test
```

The smoke test checks:

- `GET /api/health` returns a valid health payload.
- Health labels use `healthy`, `degraded`, or `unhealthy`.
- PostgreSQL, Redis, and the mock LLM report through the health response.
- `POST /api/documents` creates a document.
- `GET /api/documents` lists the uploaded document.
- `POST /api/questions` returns an answer payload.

## Manual API Calls

Check health:

```bash
curl http://localhost:8080/api/health
```

Upload a document:

```bash
curl -X POST http://localhost:8080/api/documents \
  -H "Content-Type: application/json" \
  -d '{"title":"Baseline Doc","content":"Python is known for readability and a large ecosystem."}'
```

List documents:

```bash
curl http://localhost:8080/api/documents
```

Ask a question:

```bash
curl -X POST http://localhost:8080/api/questions \
  -H "Content-Type: application/json" \
  -d '{"question":"What is Python known for?"}'
```

## Observe

```bash
make logs
```

Open:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3001`
- Dashboard: `DocuAsk Lab 1 - Baseline`

## Reset

```bash
make reset
```

This stops the stack, removes lab volumes, and starts a clean copy.

## Stop

```bash
make down
```

## Reflection Questions

1. Which dependencies must be reachable before a document upload can succeed?
2. What does the API health response say when the mock LLM is down?
3. Which work happens synchronously in the API and which work happens in the worker?
4. What would you alert on before moving this baseline toward production?
