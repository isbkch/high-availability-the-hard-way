# Reflection

## Before

With the before implementation, DocuAsk calls the LLM through `httpx.AsyncClient(timeout=None)`. When `make break` adds latency through Toxiproxy, API requests and worker embedding jobs wait behind the slow dependency. Under enough load, the service spends its capacity waiting instead of doing useful work.

## After

After `make apply-fix`, the API and worker use explicit `httpx.Timeout` budgets for connect, read, write, and pool checkout. The important result is bounded latency: the system may return an error while the LLM is slow, but it releases capacity quickly and exposes a clear degraded state.

## Root Cause

The root cause is not Toxiproxy. Toxiproxy only makes a real dependency boundary slow. The root cause is application code that did not decide how long it was willing to wait for that dependency.

When a caller has no timeout budget:

- slow dependencies consume request capacity;
- workers stay busy waiting on I/O;
- unrelated operations can become slow;
- dashboards show latency but not a deliberate failure boundary.

## Fix Pattern

Use explicit timeout budgets for every external call:

```python
timeout = httpx.Timeout(
    connect=1.0,
    read=2.0,
    write=1.0,
    pool=0.5,
)
```

Set the timeout shorter than the user-facing SLA and shorter than any retry budget. A timeout is not only a client option; it is a capacity protection decision.

## Production Checklist

- [ ] Every external HTTP call has an explicit timeout.
- [ ] Connect, read, write, and pool timeouts are considered separately.
- [ ] Timeout values are lower than the caller's SLA.
- [ ] Timeout errors are logged with dependency name and operation.
- [ ] Timeout rates are measured per dependency.
- [ ] Slow dependency behavior is visible on dashboards.
- [ ] Callers have a clear fallback, retry, or fast-fail policy.
- [ ] Worker jobs can fail without blocking the whole queue indefinitely.

## Questions

1. Which endpoint showed the most visible latency before the timeout fix?
2. What happened to worker document processing when LLM latency was injected?
3. After `make apply-fix`, did the system return success, a fast error, or degraded health?
4. What user-facing behavior would you prefer when the LLM is slow: waiting, a fast retryable error, or a fallback answer?
5. Which timeout budget would you tune first in production: connect, read, write, or pool?

Next lab: retries and jitter. Once a call can fail fast, the next question is how to retry without creating a retry storm.
