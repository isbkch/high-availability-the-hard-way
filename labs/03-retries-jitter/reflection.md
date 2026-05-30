# Reflection

## Before

With the before implementation, DocuAsk retries LLM failures immediately. The attempt count is bounded, so a single request cannot loop forever, but every attempt lands inside the same short dependency brownout. When `make load-test` restarts that brownout for each request, the before client spends the whole retry budget before the mock LLM recovers.

## After

After `make apply-fix`, the API and worker keep a visible retry budget and add exponential backoff plus jitter. The system still retries transient 429, 500, 502, 503, and 504 responses, but each caller waits before retrying and adds a small random offset so requests do not line up.

## Root Cause

The root cause is not retrying by itself. Retrying can be useful for transient failures. The root cause is retrying immediately without a time budget, backoff, jitter, or a clear list of retryable failures.

Immediate retries cause:

- extra work on an already unhealthy dependency;
- synchronized retry waves across API requests and worker jobs;
- failures that would have recovered if later attempts had waited;
- noisy failure behavior that hides the first cause;
- higher tail latency even when every individual request has a bounded attempt count.

## Fix Pattern

Use bounded retries with retryable-status filtering, explicit timeouts, exponential backoff, and jitter:

```python
MAX_RETRY_ATTEMPTS = 4
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
delay = min(max_delay, base_delay * (2 ** (attempt - 1))) + jitter
await asyncio.sleep(delay)
```

The retry budget should fit inside the caller's SLA. If the user-facing request can spend eight seconds total, do not allow retries and per-attempt timeouts to exceed that budget.

## Production Checklist

- [ ] Every external call has an explicit timeout budget.
- [ ] Retryable status codes are listed intentionally.
- [ ] Non-retryable failures fail fast.
- [ ] Retry attempts are bounded.
- [ ] Backoff grows between attempts.
- [ ] Jitter is added so callers do not synchronize.
- [ ] Retry budget fits inside the caller's SLA.
- [ ] Retry attempts, exhausted budgets, and final status are logged.
- [ ] Dashboards separate dependency errors from application errors.
- [ ] Worker retry behavior is reviewed separately from API retry behavior.

## Questions

1. Which request path showed the clearest retry storm before the fix?
2. How many LLM requests did one user-facing request create during intermittent 503s?
3. After `make apply-fix`, did failures spread out or stay synchronized?
4. Which status codes should your production LLM client retry?
5. What retry budget would fit your real user-facing SLA?
