# Reflection

## Before

With the before implementation, every `POST /api/documents` creates a new document and enqueues a new processing job. A client that retries — after a timeout, a dropped response, or the backoff added in Lab 3 — produces one document per attempt. Four retries mean four documents and four rounds of embedding through the LLM.

## After

After `make apply-fix`, the route accepts an `Idempotency-Key` header and records it in a Postgres dedupe table with a unique primary key. The first request with a given key creates the document; every retry that shares the key replays the stored result with `200` and an `Idempotent-Replay: true` header. Reusing a key with a different body returns `409`.

## Root Cause

The root cause is not retrying. Retrying is necessary for reliability. The root cause is retrying a non-idempotent write: an operation whose repeated execution produces repeated side effects. Idempotency moves the deduplication to the server so the client is free to retry safely.

Non-idempotent writes under retry cause:

- duplicate resources that users and downstream systems must reconcile;
- duplicated cost for every external call the duplicate triggers;
- data that looks corrupted but is really just repeated;
- retries that make an overloaded system do even more work.

## Fix Pattern

Use a client-supplied idempotency key plus a durable dedupe store with a unique constraint:

```python
reserve = (
    pg_insert(IdempotencyKey)
    .values(key=idempotency_key, request_hash=fingerprint)
    .on_conflict_do_nothing(index_elements=["key"])
    .returning(IdempotencyKey.key)
)
reserved = (await db.execute(reserve)).scalar_one_or_none()
```

The unique index is the concurrency guard. Reserve the key, do the work once, link the result to the key, and replay the stored result on every later attempt.

## Production Checklist

- [ ] Every non-idempotent write (create, charge, send) accepts an idempotency key.
- [ ] Keys are stored durably with a unique constraint, not in process memory.
- [ ] Concurrency is resolved by the database, not an application lock.
- [ ] Replays return the original result, not a fresh side effect.
- [ ] A key reused with a different payload is rejected, not silently replayed.
- [ ] Keys expire on a documented schedule so the store does not grow forever.
- [ ] Clients reuse the same key across retries of one logical request.
- [ ] Idempotent replays are observable (a metric or log), so silent duplication is visible.

## Questions

1. Which of your write endpoints are safe to retry today?
2. Where would you store idempotency keys, and how long would you keep them?
3. How does your client decide when to reuse a key versus mint a new one?
4. What happens in your system if the same key arrives with a different body?
5. How would you detect duplicate side effects that slipped through in the past?
