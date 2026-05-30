# High Availability The Hard Way — Design Document

**Date:** 2026-05-30
**Status:** Approved
**Author:** iLyas Bakouch

---

## Executive Summary

High Availability The Hard Way is an educational platform that teaches reliability engineering through hands-on failure labs. Learners break a real AI application, observe the consequences, understand the root cause, apply fixes, and prove the improvements work.

The platform establishes authority by demonstrating competence across three dimensions:
1. Understanding reliability theory
2. Building production-grade systems
3. Teaching failure modes through code, not slogans

---

## Vision

Become the definitive authority on building highly available AI-native systems. The brand represents hands-on, practical reliability engineering — not checklists and blog posts, but lived experience with real failures.

**Positioning statement:** "Learn production readiness the hard way — by breaking it, fixing it, and proving it works."

---

## Architecture

### Three-Layer Design

```
┌─────────────────────────────────────────────────────────────┐
│                    YouTube Channel                           │
│                  (Acquisition Engine)                        │
│              8-15 min videos per lab                         │
│                   Drives traffic →                           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Companion Documentation Site                 │
│                   (Organization Layer)                       │
│         Course TOC, concepts, checklists                     │
│              The polished front door                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     GitHub Repository                        │
│                   (Source of Truth)                          │
│            All labs, before/after code, scripts              │
│              Open for inspection, forking                    │
└─────────────────────────────────────────────────────────────┘
```

**The repo is the core. YouTube brings people in. The site organizes the journey.**

---

## DocuAsk: The Canonical Lab Application

### What It Is

A small AI document Q&A service that provides realistic failure surfaces without overwhelming complexity.

**Core user flow:**
1. Upload a document (PDF, text)
2. Background processing: chunk, embed, store
3. Ask a question
4. Retrieve relevant chunks (vector search)
5. Call LLM with context
6. Return answer

### Architecture

```
┌─────────────────┐
│  React/TS UI    │  (optional)
│      (port      │
│      3000)      │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  FastAPI API    │  (port 8080)
│   + httpx       │
└────────┬────────┘
         │
         ├──→ PostgreSQL + pgvector (port 5432)
         │    └── documents, metadata, embeddings
         │
         ├──→ Redis (port 6379)
         │    └── queue, cache
         │
         ├──→ Background Worker (Dramatiq/Celery)
         │    └── processes jobs from Redis queue
         │
         ├──→ Mock LLM Service (port 8888)
         │    └── OpenAI-compatible, controllable
         │
         └──→ Toxiproxy (port 8474)
              └── failure injection layer

Infrastructure:
├── Prometheus (port 9090)
└── Grafana (port 3001)
```

### Why This Is Perfect for Reliability Labs

| Lab Topic | DocuAsk Surface |
|-----------|-----------------|
| Timeouts | External LLM calls |
| Retries + Jitter | Intermittent LLM failures |
| Circuit Breakers | LLM/vector DB dependency failures |
| Queue Backpressure | Document upload processing |
| Idempotency | Upload retry handling |
| Health Checks | Multi-service dependency health |
| Observability | End-to-end request tracing |

---

## Lab Structure

### Directory Format

```
labs/02-timeouts/
  ├── README.md                    # Main learning path
  ├── architecture.md              # Deeper technical explanation
  ├── before/
  │   ├── api/                     # Naive implementation
  │   └── worker/
  ├── after/
  │   ├── api/                     # Fixed implementation
  │   └── worker/
  ├── scripts/
  │   ├── up.sh                    # Start all services
  │   ├── break.sh                 # Inject the failure
  │   ├── load-test.sh             # Run k6 load test
  │   ├── reset.sh                 # Reset environment
  │   └── logs.sh                  # Tail relevant logs
  ├── dashboards/
  │   └── grafana-dashboard.json   # Pre-built observability
  ├── tests/
  │   ├── test_failure_before.py   # Proves naive version breaks
  │   └── test_resilience_after.py  # Proves fix works
  └── reflection.md                # Production checklist
```

### The Learner Flow

Each lab follows the same repeatable sequence:

```
Break it → Observe it → Understand it → Fix it → Prove it
```

**Step-by-step:**

1. `make up` — Start all services
2. `make smoke-test` — Verify happy path works
3. `make break` — Trigger the failure
4. Observe via:
   - Grafana dashboards
   - API logs
   - Load test metrics
5. Read root cause explanation
6. `make apply-fix` or implement manually
7. `make break` again — See the difference
8. Review production checklist

### The First 8 Labs

| # | Lab | Failure Mode | Fix |
|---|-----|--------------|-----|
| 1 | Baseline App | None (learn the system) | — |
| 2 | Timeouts | Dependency slowness → hanging requests | Explicit httpx timeouts |
| 3 | Retries + Jitter | Intermittent failures → retry storms | Bounded retries, exponential backoff, jitter |
| 4 | Circuit Breakers | Dependency failures → cascading failure | Circuit breaker + fallback |
| 5 | Queue Backpressure | Fast producers → saturation | Bounded queues, admission control |
| 6 | Idempotency | Retries → duplicate writes | Idempotency keys |
| 7 | Health Checks | Wrong signals → bad routing | Liveness/readiness separation |
| 8 | Observability | Failures with no visibility | Structured logs, traces, metrics |

---

## Technology Stack

### Core Lab Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| API | FastAPI | Async, modern, AI-native |
| HTTP Client | httpx | Proper timeout support |
| ORM | SQLAlchemy 2.0 | Async database access |
| Database | PostgreSQL + pgvector | Data + vector storage |
| Queue/Cache | Redis | Jobs and caching |
| Workers | Dramatiq or Celery | Background processing |
| Orchestration | Docker Compose | One-command startup |
| Failure Injection | Toxiproxy | Real latency/failure injection |
| Load Testing | k6 | Performance validation |
| Metrics | Prometheus | Collection |
| Dashboards | Grafana | Visualization |
| Tracing | OpenTelemetry | Distributed tracing |
| UI (optional) | React + TypeScript | Frontend |

### Companion Site Stack (Later)

- **Generator:** Astro, Next.js, or Hugo
- **Format:** MDX for interactive docs
- **Hosting:** Vercel, Netlify, or GitHub Pages

### Video Production

- Screen recording + terminal capture
- Architecture diagrams
- 8-15 minutes per lab
- Hosted on YouTube

---

## Core Learning Principles

### The Pedagogy in One Sentence

> Break it → observe it → understand it → fix it → prove it

This creates emotional memory. The learner doesn't just read about retry storms — they cause one, watch it explode, then fix it.

### Key Principles

1. **Failures are real, not simulated**
   - Toxiproxy injects real latency
   - Real queues overflow
   - Real services crash
   - No mock failures that don't hurt

2. **Observability is part of the lesson**
   - Every failure visible in Grafana
   - Logs show the smoking gun
   - Learner develops diagnostic intuition

3. **Before/after is explicit**
   - Two code versions make difference undeniable
   - Tests prove naive version breaks
   - Tests prove fix works

4. **Production connection**
   - Every lab ends with checklist
   - "How would I detect this in prod?"
   - "What metric would alert?"

5. **Respect the learner's time**
   - `make up` and it works
   - No setup debugging
   - Clear numbered steps
   - Optional videos for acceleration

---

## Repository Structure

```
high-availability-the-hard-way/
├── README.md                          # Project overview, quick start
├── LICENSE
├── CONTRIBUTING.md
│
├── docuask/                          # The canonical app
│   ├── api/                          # FastAPI service
│   ├── worker/                       # Background jobs
│   ├── frontend/                     # React/TS UI (optional)
│   └── docker-compose.yml            # Base stack
│
├── labs/
│   ├── 01-baseline-app/
│   │   ├── README.md
│   │   ├── before/
│   │   ├── after/
│   │   ├── scripts/
│   │   ├── dashboards/
│   │   └── tests/
│   │
│   ├── 02-timeouts/
│   ├── 03-retries-jitter/
│   ├── 04-circuit-breakers/
│   ├── 05-queue-backpressure/
│   ├── 06-idempotency/
│   ├── 07-health-checks/
│   └── 08-observability/
│
├── docs/                             # Companion documentation
│   ├── concepts/
│   │   ├── timeouts.md
│   │   ├── retries.md
│   │   ├── circuit-breakers.md
│   │   └── ...
│   ├── case-studies/
│   └── checklists/
│       └── production-readiness.md
│
├── scripts/                          # Shared utilities
│   ├── setup.sh                      # Initial environment setup
│   └── test-all-labs.sh              # CI for lab integrity
│
└── .github/
    └── workflows/
        └── test-labs.yml             # Ensure labs still work
```

**Organizational principles:**
- Labs numbered in learning order
- Each lab self-contained
- `docuask/` adapted per lab
- Shared scripts for common operations
- Docs alongside for easy updates

---

## Launch Scope: MVP

### Day 1 — What You Actually Need

**GitHub repository with 3 complete labs:**
1. `01-baseline-app` — Working system, learn the architecture
2. `02-timeouts` — First real failure lesson
3. `03-retries-jitter` — Shows the escalation pattern

**Solid README explaining:**
- What this project is
- Why it matters
- How to start
- The philosophy

**3 companion videos (8-15 min each):**
- YouTube channel launches with these
- Establish brand voice
- Drive traffic to repo

**Basic companion site:**
- Landing page explaining the project
- Links to labs and videos
- "Why high availability matters"
- Built with Astro/Next.js, deployed to Vercel

### Day 1 NOT To Do

- ❌ Custom interactive platform (comes later if demand exists)
- ❌ All 8 labs (finish 3, iterate based on feedback)
- ❌ Production video studio (screen recording + diagrams are fine)
- ❌ Complex site features (just a good landing page)

### Day 1 Success Criteria

- Someone can clone, run `make up`, break something, fix it, in <30 minutes
- The repo looks professional and authoritative
- The videos feel like a real course

### After Day 1

Iterate based on feedback:
- Add labs 4-8 one at a time
- Improve companion site
- Refine pedagogy based on learner feedback

---

## Design Principles and Constraints

### Non-Negotiable Principles

1. **Educational first, tool second**
   - The repo teaches, it doesn't just automate
   - Every design choice serves learning outcomes
   - Authority comes from pedagogy, not features

2. **Failures must be real**
   - No fake simulations
   - Toxiproxy for real latency
   - Real queue saturation
   - Learner must feel the pain

3. **Setup must be trivial**
   - `make up` is all it takes
   - No version troubleshooting
   - Docker everything
   - One command to verify

4. **Prove everything**
   - Tests show naive version breaks
   - Tests show fix works
   - Load tests demonstrate difference
   - No hand-waving

### Constraints

1. **No polyglot at launch**
   - Python/FastAPI only
   - Don't dilute the learning experience
   - Go/Node labs later as bonuses

2. **No custom platform at launch**
   - GitHub is fine for now
   - Interactive platform only after proving demand
   - Don't build product surface before authority

3. **Reuse existing rag-starter-kit**
   - Don't rebuild from scratch
   - Adapt what already works
   - Focus on reliability patterns, not scaffolding

---

## Production Readiness Checklist (Per Lab)

Each lab ends with these questions:

**For the Timeout Lab:**
- [ ] Do all external calls have explicit timeouts?
- [ ] Are connect/read/write/pool timeouts configured separately?
- [ ] Are timeout errors logged with enough context?
- [ ] Does the caller degrade gracefully?
- [ ] Is the timeout shorter than the upstream SLA?
- [ ] Are dashboards showing timeout rate and dependency latency?

**For the Retry Lab:**
- [ ] Are retries bounded (max attempts)?
- [ ] Is there exponential backoff?
- [ ] Is jitter applied to avoid thundering herd?
- [ ] Are retry budgets configured?
- [ ] Are retries only on idempotent operations?
- [ ] Are retry storms visible in metrics?

**For the Circuit Breaker Lab:**
- [ ] Is there a circuit breaker on external dependencies?
- [ ] Is there a fallback behavior?
- [ ] Are circuit state transitions logged?
- [ ] Is the breaker configured with appropriate thresholds?
- [ ] Does the system auto-recover when dependency heals?

And so on for each lab.

---

## Success Metrics

**Day 1-30:**
- GitHub stars: 100+
- Video views: 500+ per video
- Site visitors: 200+
- People completing labs: 20+

**Day 30-90:**
- GitHub stars: 500+
- Video views: 2,000+ per video
- Community contributions: 5+
- Labs 4-6 launched

**Day 90+:**
- Establish as go-to resource for AI reliability
- Guest posts, conference talks based on content
- Lab contributions from community
- Consider interactive platform if demand proven

---

## Next Steps

1. **Write implementation plan** — Detailed steps for Day 1 MVP
2. **Build DocuAsk base app** — Adapt rag-starter-kit
3. **Create Lab 1** — Baseline with no failure
4. **Create Lab 2** — Timeouts with full before/after
5. **Create Lab 3** — Retries with jitter
6. **Build companion site** — Simple landing page
7. **Record 3 videos** — Screen + diagrams
8. **Launch** — YouTube, GitHub, site all at once

---

## Appendix: Anti-Patterns Detected

This is the master list of reliability anti-patterns the platform will teach:

1. Missing timeouts on HTTP/database calls
2. Retries without exponential backoff or jitter
3. Unbounded queues
4. No idempotency key on write endpoints
5. No graceful shutdown handler
6. No readiness/liveness distinction
7. Database migrations that are not backward compatible
8. Missing structured logs around critical paths
9. No circuit breaker around external dependencies
10. No rate limiting on public endpoints
11. No SLO/error-budget metadata
12. Dangerous default config
13. Hardcoded credentials/secrets
14. Missing alerting hooks
15. No fallback behavior for external API failure

Each anti-pattern becomes one or more labs.

---

*End of Design Document*
