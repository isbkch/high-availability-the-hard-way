# High Availability The Hard Way

Learn production readiness the hard way: by breaking a real application, observing the failure, fixing the root cause, and proving the fix works.

This repository is an educational reliability engineering platform. The Day 1 MVP is built around DocuAsk, a small AI document Q&A service with the same failure surfaces that show up in production AI systems: external LLM calls, vector search, background jobs, Redis queues, Postgres storage, timeouts, retries, and observability.

## The Teaching Loop

Break it -> Observe it -> Understand it -> Fix it -> Prove it

Each lab is a runnable workshop. You start a local stack, verify the happy path, inject a specific failure, watch how the system degrades, apply the fix, and rerun the proof. The point is not to memorize a checklist. The point is to build operational judgment from a failure you can reproduce.

## Project Shape

The GitHub repository is the source of truth. It contains the lab code, before/after implementations, scripts, tests, dashboards, and production checklists.

The companion site organizes the journey. It gives the labs a course-like table of contents and links concepts back to the runnable source.

YouTube is the acquisition engine. Videos are meant to explain the narrative and drive learners back to the repo, where the claims can be inspected and run.

## DocuAsk

DocuAsk is the canonical lab application:

1. Upload a document.
2. Process it in a background worker.
3. Chunk and embed the content.
4. Store document chunks in Postgres with pgvector.
5. Ask a question.
6. Retrieve relevant chunks.
7. Call an OpenAI-compatible mock LLM.
8. Return an answer with sources.

The app is intentionally small, but the reliability problems are real enough to matter. A slow LLM call can hang the API. Immediate retries can exhaust a retry budget before a dependency recovers. A worker can fail differently than the request path. Grafana and Prometheus are part of the lesson, not decoration.

## Day 1 Labs

| # | Lab | Failure Mode | Fix / Lesson | Path |
|---|-----|--------------|--------------|------|
| 1 | Baseline App | No injected failure | Learn the stack, API routes, worker path, and dashboards | `labs/01-baseline-app` |
| 2 | Timeouts | Slow dependency calls pin requests and jobs | Explicit `httpx.Timeout` budgets in API and worker code | `labs/02-timeouts` |
| 3 | Retries + Jitter | Transient LLM 503s trigger immediate retry storms | Bounded retries with retryable statuses, exponential backoff, and jitter | `labs/03-retries-jitter` |

Future labs are intended to cover circuit breakers, queue backpressure, idempotency, health checks, and observability.

## Quick Start

Prerequisites:

- Docker Desktop or Docker Engine with Compose
- Python 3.11+
- `uv` for Python environment and dependency installation
- `make`

Run the baseline lab:

```bash
cd labs/01-baseline-app
make up
make smoke-test
```

Run a failure lab:

```bash
cd labs/02-timeouts
make up
make smoke-test
make break
make load-test
make apply-fix
make load-test
make reset
```

The same pattern applies to `labs/03-retries-jitter`.

Useful endpoints while a lab is running:

- API: http://localhost:8080
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3001
- Mock LLM: http://localhost:8888

Grafana uses `admin` / `admin` in the local lab stack.

## Repository Map

```text
docuask/                 Shared FastAPI, worker, models, schemas, and vector code
shared/                  Shared Docker Compose, Grafana, Prometheus, and scripts
labs/01-baseline-app/    Happy-path DocuAsk workshop
labs/02-timeouts/        Slow LLM dependency and explicit timeout budgets
labs/03-retries-jitter/  Transient 503 brownouts and retry backoff with jitter
docs/superpowers/        Planning and design artifacts from the build process
site/                    Companion site, added after the Day 1 labs
```

## Verification

Static checks and unit tests are designed to run without a Docker daemon:

```bash
python3 -m pytest docuask/tests tests labs/01-baseline-app/tests labs/02-timeouts/tests labs/03-retries-jitter/tests -q
bash -n shared/scripts/*.sh labs/01-baseline-app/scripts/*.sh labs/02-timeouts/scripts/*.sh labs/03-retries-jitter/scripts/*.sh
docker compose -f shared/docker-compose.yml config --quiet
docker compose -f labs/01-baseline-app/docker-compose.yml config --quiet
docker compose -f labs/02-timeouts/docker-compose.yml config --quiet
docker compose -f labs/03-retries-jitter/docker-compose.yml config --quiet
```

Runtime lab tests are opt-in because they need the relevant Docker Compose stack running:

```bash
RUN_LAB_RUNTIME_TESTS=1 python3 -m pytest labs/02-timeouts/tests/test_resilience_after.py
RUN_LAB_RUNTIME_TESTS=1 python3 -m pytest labs/03-retries-jitter/tests/test_resilience_after.py
```

## Design Principles

- The failure must be observable from the outside, not just described in prose.
- The before state must fail for a specific reason.
- The after state must prove the fix with the same script or test.
- API and worker behavior are both part of the reliability contract.
- Metrics, logs, and dashboards are teaching material.
- The repo should remain runnable, inspectable, and forkable.

## Status

Day 1 currently includes the shared lab infrastructure, DocuAsk core, API and worker, Lab 1 baseline, Lab 2 timeouts, and Lab 3 retries with jitter. Companion site and video packaging are next.
