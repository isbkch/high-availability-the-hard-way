# Lab 2: Timeouts

This lab shows why every network dependency call needs an explicit timeout. DocuAsk talks to a mock OpenAI-compatible LLM through Toxiproxy. You will inject latency and compare the no-timeout implementation with an implementation that uses explicit connect/read/write/pool timeout budgets.

## Flow

```bash
make up
make smoke-test
make break
make load-test
make apply-fix
make load-test
make reset
```

Expected behavior:

- Before `make apply-fix`, the API and worker use `httpx.AsyncClient()` without an explicit timeout. Injected LLM latency can tie up request and worker paths.
- After `make apply-fix`, the API and worker use `httpx.Timeout(connect=..., read=..., write=..., pool=...)`. Injected latency should fail fast instead of creating unbounded latency.
- `make reset` restores the before implementation and removes the latency toxic.

## Runtime Patch Model

The `api` and `worker` services bind-mount `../../docuask:/app/docuask`. The lab scripts copy files from `before/` or `after/` into the host `docuask` package, then restart the containers so the change is active. This keeps all lab-owned source files under `labs/02-timeouts/` while making the failure and fix observable at runtime.

## Endpoints

- API: http://localhost:8080
- Health: `GET /api/health`
- Upload document: `POST /api/documents`
- List documents: `GET /api/documents`
- Get document: `GET /api/documents/{document_id}`
- Ask question: `POST /api/questions`
- Toxiproxy API: http://localhost:8474
- Toxiproxy LLM proxy: http://localhost:8666
- Mock LLM direct: http://localhost:8888/v1/models
- Grafana: http://localhost:3001, `admin` / `admin`

Health labels are `healthy`, `degraded`, and `unhealthy`.

## Failure Injection

`make break` creates a Toxiproxy latency toxic with:

- `POST /proxies/mock-llm/toxics`
- toxic name `llm-latency`
- toxic type `latency`

`make reset` removes it with:

- `DELETE /proxies/mock-llm/toxics/llm-latency`

## Cleanup

```bash
make down
```
