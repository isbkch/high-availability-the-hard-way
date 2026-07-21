# Lab 4: Idempotency

This lab shows why retries are only safe when the server is idempotent. In Lab 3 you gave DocuAsk a retrying client. Here, a client that retries `POST /api/documents` — because of a timeout, a dropped connection, or the backoff you added in Lab 3 — submits the same document several times. Without idempotency, DocuAsk creates a new document and runs a fresh round of embedding for every retry: duplicate data and duplicate cost.

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

- Before `make apply-fix`, four identical submissions create four documents and trigger four rounds of embedding. `make load-test` exits non-zero because it detects duplicate documents.
- After `make apply-fix`, the same four submissions share one `Idempotency-Key`. The first creates the document; the rest replay the stored result. `make load-test` exits zero.
- `make reset` restores the before implementation and clears the dedupe table.

## Runtime Patch Model

The `api` and `worker` services bind-mount `../../docuask:/app/docuask`. The lab scripts copy `before/docuask/api/routes/documents.py` or `after/docuask/api/routes/documents.py` into the host `docuask` package, then restart the containers. All lab-owned source stays under `labs/04-idempotency/`.

## Endpoints

- API: http://localhost:8080
- Health: `GET /api/health`
- Upload document: `POST /api/documents` (send an `Idempotency-Key` header to deduplicate retries after the fix)
- List documents: `GET /api/documents`
- Get document: `GET /api/documents/{document_id}`
- Ask question: `POST /api/questions`
- Mock LLM direct: http://localhost:8888/v1/models
- Mock LLM state: http://localhost:8888/mock-state
- Grafana: http://localhost:3001, `admin` / `admin`

## Failure Injection

There is no network fault in this lab. The fault is the retrying client. `make break` resets the mock LLM request counter and announces that `make load-test` will submit the same document `RETRIES` (default 4) times with a single `Idempotency-Key`, exactly as a retrying HTTP client would.

## The Fix

`after/docuask/api/routes/documents.py` reads the `Idempotency-Key` header and reserves it in a Postgres `idempotency_keys` table using `INSERT … ON CONFLICT (key) DO NOTHING`. The unique primary key is the race guard:

- First request with a key: create the document, link it to the key, return `201`.
- Retry with the same key and body: replay the stored document, return `200` with header `Idempotent-Replay: true`.
- Same key with a different body: return `409 Conflict`.

## Cleanup

```bash
make down
```
