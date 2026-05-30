# Lab 3: Retries and Jitter

This lab shows how retry behavior can protect or damage availability. DocuAsk talks to a lab-local OpenAI-compatible mock LLM. `make break` switches that mock into a deterministic transient 503 brownout, then `make load-test` restarts that short brownout for each user-facing request so you can compare immediate retries with exponential backoff and jitter.

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

- Before `make apply-fix`, the API and worker have a bounded attempt count but retry immediately. The code is not infinite, but intermittent 503s can still align callers into a retry storm.
- After `make apply-fix`, the API and worker use retryable-status filtering, explicit timeout budgets, exponential backoff, and jitter.
- `make reset` restores the before implementation and disables the mock LLM failure mode.
- `make load-test` exits non-zero before the fix and exits zero after the fix.

## Runtime Patch Model

The `api` and `worker` services bind-mount `../../docuask:/app/docuask`. The lab scripts copy files from `before/` or `after/` into the host `docuask` package, then restart the containers so the change is active. This keeps all lab-owned source files under `labs/03-retries-jitter/` while making the failure and fix observable at runtime.

## Endpoints

- API: http://localhost:8080
- Health: `GET /api/health`
- Upload document: `POST /api/documents`
- List documents: `GET /api/documents`
- Get document: `GET /api/documents/{document_id}`
- Ask question: `POST /api/questions`
- Mock LLM direct: http://localhost:8888/v1/models
- Mock LLM state: http://localhost:8888/mock-state
- Grafana: http://localhost:3001, `admin` / `admin`

Health labels are `healthy`, `degraded`, and `unhealthy`.

## Failure Injection

`make break` enables a deterministic short brownout with:

- `POST /control/failure-mode`
- body `{"mode":"brownout_503","every_n":2,"brownout_seconds":0.45}`

During the brownout, the mock returns 503 for every LLM request. Immediate retries spend the whole retry budget before the dependency recovers. Backoff plus jitter waits long enough for a later attempt to land after recovery.

`make reset` disables failures with:

- `POST /control/reset`

The mock also supports `alternating_503` and `every_nth_503` for demonstrations that need a different deterministic cadence.

## Cleanup

```bash
make down
```
