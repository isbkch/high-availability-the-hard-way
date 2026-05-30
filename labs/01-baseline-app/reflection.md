# Reflection: Baseline Application

## What The Baseline Shows

- The API depends on PostgreSQL, Redis, and the LLM path for a fully healthy response.
- Document upload is not just a database write; it must enqueue work successfully.
- Question answering depends on embeddings, vector search, and chat completion.
- A healthy startup does not prove the system is production-ready.

## Production Readiness Checklist

### Observability

- [ ] Structured logs include request IDs and document IDs.
- [ ] API, worker, database, queue, and LLM latency are visible.
- [ ] Error rates are separated by dependency and route.
- [ ] Dashboards distinguish user-facing failures from background failures.

### Reliability

- [ ] External calls have explicit timeouts.
- [ ] Retries use backoff and jitter.
- [ ] Circuit breakers protect known dependency boundaries.
- [ ] Health checks distinguish readiness from liveness.
- [ ] The worker shuts down gracefully without losing in-flight jobs.

### Data Safety

- [ ] Uploads are idempotent where callers may retry.
- [ ] Failed document processing leaves inspectable error state.
- [ ] Database migrations are reversible or safely forward-only.
- [ ] Backups and restore drills exist.

### Operations

- [ ] Queue depth has an alert threshold.
- [ ] Dependency outages have runbooks.
- [ ] Secrets are not hardcoded.
- [ ] Capacity limits are known before load increases.

## Next Lab

Lab 2 introduces timeout failures so you can see how a slow dependency affects the baseline.
