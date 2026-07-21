# Architecture

## The duplicate-work path

`POST /api/documents` creates a `Document` row and enqueues a Dramatiq job that chunks and embeds the content through the mock LLM. The endpoint is cheap and returns quickly, so a client that times out or retries will send the request again. In the before implementation every call is unconditional: N retries create N documents and N embedding rounds.

This is the failure mode that retries (Lab 3) can amplify. Retrying a non-idempotent write turns one logical intent — "store this document" — into many side effects.

## The idempotency key

The after implementation accepts a client-supplied `Idempotency-Key` header. The key names the intent, not the attempt, so every retry of the same submission carries the same key.

Server side, the key is stored in a Postgres `idempotency_keys` table whose primary key is the key itself. The route reserves the key with:

```sql
INSERT INTO idempotency_keys (key, request_hash) VALUES ($1, $2)
ON CONFLICT (key) DO NOTHING
RETURNING key;
```

- If the insert returns a row, this request won the reservation and does the work exactly once, then links the created `document_id` back to the key row.
- If the insert returns nothing, a prior request owns the key. The route reads the stored row and replays the same document (`200` + `Idempotent-Replay: true`), or returns `409` if the same key arrived with a different request body.

The unique primary key does the hard part. Two concurrent retries race to insert the same key; Postgres lets exactly one win. No application lock is required.

## Why store a request hash

The `request_hash` column is a sha256 of the request body. It catches a real client bug: reusing an idempotency key for a different payload. Returning `409` there is safer than silently replaying the wrong resource.

## The replay poll

If a retry loses the reservation before the winner has linked its `document_id` (only possible under true concurrency), the loser briefly polls the key row until the link appears. The lab's load test retries sequentially, so this branch is not normally exercised; it exists so the implementation is correct under concurrent retries.

## Observability

The mock LLM counts embedding and chat requests and exposes them at `/mock-state`. Before the fix the embedding counter climbs with every duplicate document; after the fix it climbs once per unique submission. Prometheus and Grafana probe API and dependency health.
