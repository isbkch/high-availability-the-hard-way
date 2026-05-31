# YouTube Script — “Your AI-generated App is Not production Ready”

## Video Title

Your AI-generated App is Not production Ready

## Core Promise

AI can generate working software quickly, but production readiness requires engineering judgment: timeouts, retries, health checks, observability, fallback behavior, and recovery paths.

## Target Length

12–15 minutes

## Recording Setup

- A-roll: Talking head, direct to camera.
- Screen recording: Terminal, code editor, simple app demo, diagrams, repo.
- B-roll: Typing, looking at logs, architecture sketch, coffee/desk shots, server/dashboard shots, whiteboard, close-ups of keyboard, monitor, notebook.

---

# 0:00–0:35 — Cold Open

## A-ROLL — Talking Head

AI can now generate a full application in minutes.

Frontend. Backend. API routes. Database schema. Dockerfile. Deployment config. Maybe even tests.

And that is impressive.

But there is a dangerous gap that almost nobody talks about.

An app can work perfectly in a demo…

…and still be completely unfit for production.

Today, I’m going to show you why.

We’re going to take a simple AI-generated app that works, and we’re going to ask the questions production will ask:

What happens when a dependency becomes slow?

What happens when retries multiply traffic?

What happens when the app says it is healthy, but users cannot actually use it?

And by the end, you’ll understand the difference between software that works…

…and software that survives.

## B-ROLL / SCREEN

- Fast cuts:
  - ChatGPT/Cursor/Codex generating app code.
  - Terminal: npm run dev, docker compose up.
  - Browser showing app working.
  - Cut suddenly to terminal errors/timeouts.
  - Dashboard with red graph or logs scrolling.
- On-screen text:
  - “WORKING ≠ PRODUCTION READY”
  - “Happy path is not production.”

---

# 0:35–1:20 — Reset the Frame

## A-ROLL — Talking Head

Before we go further, let me be clear.

This is not an anti-AI video.

I use AI. I like AI. I think every engineer should learn how to use it well.

But AI changes the bottleneck.

The bottleneck is no longer just: “Can you write the code?”

The bottleneck becomes: “Do you understand what can go wrong after the code works?”

That is where production engineering starts.

And this is also why I’m building a new open-source project called High Availability The Hard Way.

The goal is simple:

Build a real application.

Break it under realistic production failures.

Then harden it step by step.

## B-ROLL / SCREEN

- Screen recording of GitHub repo homepage: high-availability-the-hard-way.
- Slowly scroll README.
- Highlight phrase:
  - “Build. Break. Harden.”
- Cut to terminal with folders:
  - labs/
  - docuask/
  - shared/
  - site/
  - youtube/

---

# 1:20–2:25 — Define the Problem

## A-ROLL — Talking Head

Most tutorials stop too early.

They show you how to create the app.

They show you how to run it locally.

They show you the happy path.

Click button. Send request. Get response. Done.

But production does not care about your happy path.

Production cares about the unhappy path.

What happens when the database is slow?

What happens when your AI provider starts timing out?

What happens when Redis is unavailable?

What happens when 200 users hit the same endpoint at the same time?

What happens when every failed request retries three times?

What happens when your health check returns 200 OK, but the main user flow is broken?

These are the questions that separate a demo from a system.

## B-ROLL / SCREEN

- Simple architecture diagram:
  - User → Frontend → API → Database
  - API → AI Provider
  - API → Vector DB
  - API → Redis
- Then overlay red warning icons on:
  - AI Provider
  - Vector DB
  - Database
  - Redis
- On-screen text:
  - “Production asks different questions.”

---

# 2:25–3:45 — Show the Working App

## SCREEN RECORDING — App Demo

Narration over screen.

Here is the app.

For this demo, imagine we have a simple AI document assistant.

Nothing crazy.

A frontend.

An API.

A database.

Redis for caching.

A vector database for retrieval.

And an external AI provider to generate the answer.

I upload a document.

I ask a question.

The backend retrieves the relevant chunks.

The AI provider generates the answer.

And the user gets a response.

From the outside, everything looks fine.

The app works.

## B-ROLL / SCREEN

- Show the app UI.
- Upload or select a document.
- Ask a simple question.
- Show successful response.
- Show terminal logs:
  - request received
  - retrieval completed
  - AI response generated
  - 200 OK
- On-screen text:
  - “The happy path works.”

## A-ROLL — Talking Head

And this is exactly where most people stop.

Especially now with AI-generated apps.

The app runs.

The feature works.

The demo looks good.

So the instinct is to say: ship it.

But this is where the dangerous part begins.

Because “it works” only tells you one thing:

The happy path succeeded once.

It does not tell you how the system behaves under failure.

---

# 3:45–5:35 — Failure Mode 1: Slow Dependency

## A-ROLL — Talking Head

Let’s start with one of the most common production failures.

Not a dependency that goes completely down.

A dependency that becomes slow.

This is worse than a clean failure.

Because when something is down, you usually get an error quickly.

But when something is slow, your system waits.

And waits.

And waits.

Requests pile up.

Threads or workers get occupied.

Connection pools get exhausted.

Queues grow.

Users refresh the page.

And now your system is under even more pressure.

## SCREEN RECORDING

Narration over screen.

Let’s simulate that.

I’m going to make the AI provider slow.

Something like this:

```bash
cd labs/02-timeouts
make break
make load-test
```

Now I’ll send a normal request.

The user asks a question.

The frontend is waiting.

The API is waiting.

The backend worker is waiting.

Nothing is technically “crashing.”

But from the user’s perspective, the app is broken.

## B-ROLL / SCREEN

- Terminal:
  - cd labs/02-timeouts
  - make break
  - make load-test
  - requests wait on the slow mock LLM before the fix
- Browser shows loading spinner.
- Logs show slow response.
- Optional visual overlay:
  - “Dependency slow”
  - “API waiting”
  - “User waiting”
- Show simple diagram with traffic backing up.

## A-ROLL — Talking Head

This is the first lesson:

A timeout is not just a performance setting.

A timeout is a reliability boundary.

When you call another service, you are basically saying:

“I am willing to wait this long, but not longer.”

Without that boundary, your app can be held hostage by any slow dependency.

That dependency could be an AI provider.

It could be a payment provider.

It could be an internal service.

It could be a database query.

The principle is the same.

No timeout means no boundary.

No boundary means failure can spread.

## B-ROLL / SCREEN

- Code editor:
  - Show HTTP call without timeout.
- Highlight:
  - await client.post(...)
  - no timeout configured.
- Then show corrected example:
  - timeout added.
- On-screen text:
  - “Timeouts create failure boundaries.”

---

# 5:35–7:35 — Failure Mode 2: Bad Retries

## A-ROLL — Talking Head

Now the obvious reaction is:

Okay, let’s add retries.

And retries are useful.

Retries can turn temporary failures into successful requests.

But retries are also dangerous.

Because retries multiply traffic.

If one request fails and retries three times, that is now four attempts.

If 100 requests fail and each retries three times, that is 400 attempts.

If the dependency was already struggling, your retry logic may be the thing that finishes it off.

## SCREEN RECORDING

Narration over screen.

Let’s simulate that.

In the retries lab, I’m going to switch the mock AI provider into a short 503 brownout.

Now the app starts retrying.

At first, this looks reasonable.

Request fails.

Try again.

Fails again.

Try again.

But now watch the logs.

One user request creates multiple backend calls.

Multiple users create a wave of retries.

The system is not recovering.

It is attacking itself.

## B-ROLL / SCREEN

- Terminal showing repeated retry logs:
  - cd labs/03-retries-jitter
  - make break
  - make load-test
  - attempt=1
  - attempt=2
  - attempt=3
  - transient 503
- Simple graph or terminal counter showing increasing request count.
- Diagram:
  - One user request fans out into multiple retry attempts.
- On-screen text:
  - “Retries multiply load.”

## A-ROLL — Talking Head

This is why retries need rules.

You need a maximum number of attempts.

You need exponential backoff.

You need jitter, so every client does not retry at the exact same time.

You need to know which failures are retryable and which are not.

And if the operation changes state, you need idempotency.

Because retrying a read is one thing.

Retrying a payment, an order, a booking, a message send, or a database write is very different.

## B-ROLL / SCREEN

- Code editor:
  - Show naive retry loop.
- Highlight:
  - for attempt in range(3)
  - no backoff
  - no jitter
  - no idempotency
- Then show improved pseudo-code:
  - max_attempts
  - backoff
  - jitter
  - timeout
  - idempotency_key
- On-screen text:
  - “Retries without backoff are not resilience.”

## A-ROLL — Talking Head

That is the second lesson:

Retries without backoff are not resilience.

They are denial-of-service against your own system.

---

# 7:35–9:45 — Future Lab: Fake Health Checks

## A-ROLL — Talking Head

Now let’s talk about health checks.

This one is subtle.

This is not one of the Day 1 labs yet.

The repo already has a basic dependency-aware health endpoint, and that is intentional.

It reports the state of the database, Redis, and the mock LLM.

But the dedicated liveness and readiness lab comes later in the series.

For now, I want to show the production question that future lab is going to answer.

A lot of apps have a /health endpoint that returns something like:

“OK.”

And because it returns 200, the load balancer thinks the service is healthy.

Kubernetes thinks the container is healthy.

The deployment system thinks everything is fine.

But the user still cannot complete the main action.

So the system is technically up…

…but functionally broken.

## SCREEN RECORDING

Narration over screen.

Here is the health endpoint.

```bash
curl http://localhost:8080/api/health
```

In this repo, it returns a dependency-aware response, something like:

```json
{
  "status": "healthy",
  "database": "healthy",
  "redis": "healthy",
  "llm": "healthy"
}
```

That is already better than a bare “OK.”

But it still raises the real production question:

What decision is this endpoint supposed to drive?

If Kubernetes calls it, should a failure restart the process?

If a load balancer calls it, should a failure remove this instance from traffic?

If an operator calls it during an incident, should it explain whether users can ask questions?

So what does health really mean here?

Does it mean the process is running?

Does it mean the API can accept traffic?

Does it mean the full product experience works?

Those are not the same question.

## B-ROLL / SCREEN

- Terminal:
  - curl http://localhost:8080/api/health
  - { "status": "healthy", "database": "healthy", "redis": "healthy", "llm": "healthy" }
- Code/editor:
  - show `docuask/api/routes/health.py`
  - point out that this is dependency health, not separate liveness/readiness yet.
- Split screen:
  - left: one `/api/health` endpoint
  - right: future lab labels: `/live`, `/ready`, dependency health, synthetic user-flow check.
- On-screen text:
  - “One health endpoint cannot answer every health question.”

## A-ROLL — Talking Head

This is why production systems often separate different kinds of health.

A liveness check answers:

“Should this process be restarted?”

A readiness check answers:

“Should this instance receive traffic?”

A dependency check answers:

“Are the things I depend on available enough for this service to do its job?”

And a user-facing check asks:

“Can the user complete the critical workflow?”

If you mix those together, your automation can make bad decisions.

It might send traffic to an instance that is not ready.

It might restart a process that is actually fine.

Or it might declare the system healthy while users are failing.

## B-ROLL / SCREEN

- Simple table on screen:
  - Liveness: “Should I restart?”
  - Readiness: “Should I receive traffic?”
  - Dependency health: “Can I do my job?”
  - Synthetic check: “Can users complete the workflow?”
- Optional: Show code file:
  - future lab sketch: /live, /ready, /health/dependencies

## A-ROLL — Talking Head

That is the third lesson:

High availability is not whether your container is running.

It is whether users can still accomplish the job they came to do.

And that is why health checks get their own future lab instead of being treated as a checkbox in this overview.

---

# 9:45–11:20 — What Production-Ready Actually Means

## A-ROLL — Talking Head

So when someone says “production-ready,” I do not think the first question should be:

“Does it deploy?”

That matters.

But it is not enough.

The better questions are:

What are the critical user journeys?

What can fail?

How does the system behave when it fails?

How quickly can we detect the failure?

How quickly can we recover?

Can the system degrade gracefully?

Can we deploy safely?

Can we roll back safely?

Do we know the blast radius?

Do we have logs, metrics, and traces that explain what happened?

Do we have alerts that point to user impact, not just noisy infrastructure symptoms?

That is production readiness.

It is not one tool.

It is not Kubernetes.

It is not AWS.

It is not Terraform.

It is not a YAML file.

It is a discipline.

## B-ROLL / SCREEN

- Show checklist animation or slide:
  - Failure modes
  - Timeouts
  - Retries
  - Circuit breakers
  - Backpressure
  - Idempotency
  - Health checks
  - Observability
  - Rollback
  - Recovery
- Cut to you writing “Failure Modes” on paper or whiteboard.
- On-screen text:
  - “Production readiness is a discipline.”

---

# 11:20–12:40 — Introduce High Availability The Hard Way

## A-ROLL — Talking Head

This is exactly why I’m building High Availability The Hard Way.

The idea is not to create another checklist that people bookmark and never use.

The idea is to build a hands-on lab.

We start with an application that works.

Then we break it.

Then we harden it.

Each lab focuses on one failure mode.

Timeouts.

Retries.

Circuit breakers.

Health checks.

Queues and backpressure.

Idempotency.

Observability.

Zero-downtime deployments.

Disaster recovery.

And the goal is to understand not just what to configure, but why the pattern exists in the first place.

## SCREEN RECORDING

Narration over screen.

Inside the repo, the structure will look something like this:

```text
high-availability-the-hard-way/
  docuask/
    api/
    worker/
    vector/
  labs/
    01-baseline-app/
    02-timeouts/
    03-retries-jitter/
  shared/
    prometheus/
    grafana/
    scripts/
  site/
  youtube/
```

Each lab will have the same pattern:

Build.

Break.

Observe.

Fix.

Run it again.

## B-ROLL / SCREEN

- GitHub repo.
- File tree.
- README.
- You typing a commit message.
- Terminal:
  - make up
  - make break
  - make load-test
  - make apply-fix
  - make load-test
- On-screen text:
  - “Build. Break. Harden.”

---

# 12:40–13:50 — Why This Matters in the AI Era

## A-ROLL — Talking Head

The reason I think this matters now is because AI is making it easier than ever to create software.

That is good.

But it also means more people will ship systems they do not fully understand.

More generated code.

More generated infrastructure.

More generated APIs.

More generated deployment pipelines.

But when that system fails in production, the user does not care whether the code was written by a human or by AI.

The business does not care.

The customer does not care.

The incident does not care.

The only thing that matters is:

Can you understand the system?

Can you reason about the failure?

Can you restore service?

Can you prevent the same failure from happening again?

That is the skill.

## B-ROLL / SCREEN

- Screen recording of AI generating code.
- Cut to logs/errors.
- Cut to diagram of failure spreading.
- Cut to you looking at dashboards.
- On-screen text:
  - “AI changes the bottleneck.”
  - “The new bottleneck is judgment.”

## A-ROLL — Talking Head

AI can help you move faster.

But speed without reliability just gets you to the outage faster.

So the future does not belong only to people who can generate code.

It belongs to people who can generate code, understand the system, and make it survive reality.

---

# 13:50–14:45 — Closing CTA

## A-ROLL — Talking Head

So this is the beginning of the series.

The title is High Availability The Hard Way.

We are going to build real systems, break them in realistic ways, and harden them step by step.

The repo is linked below.

If you want to do one thing after this video, do this:

Clone the repo and run Lab 2.

It is the timeout lab.

You will start the app.

You will inject a slow AI provider.

You will watch the request path degrade.

Then you will apply the timeout fix and run the same proof again.

Because one missing timeout can take down your entire app.

And once you see it happen, you will never look at production code the same way again.

## B-ROLL / SCREEN

- GitHub repo page.
- README section: “Start Here From Video 1”
- Terminal:
  - git clone https://github.com/isbkch/high-availability-the-hard-way.git
  - cd high-availability-the-hard-way
  - cd labs/02-timeouts
  - make up
  - make smoke-test
  - make break
  - make load-test
  - make apply-fix
  - make load-test
- On-screen text:
  - “Run Lab 2: Timeouts”
  - “Clone. Break. Fix. Prove.”
- Fade out with repo name:
  - high-availability-the-hard-way

---

# Optional Ending Line

## A-ROLL — Talking Head

Remember:

A working demo proves that the happy path works.

Production readiness proves that the system can survive when the happy path disappears.

---

# Shorts / Clips to Extract

## Short 1 — “Working does not mean production-ready”

Use the opening section.

Clip title:

Your AI App Works. That Means Almost Nothing.

## Short 2 — “Retries can kill your app”

Use the retry storm section.

Clip title:

Retries Without Backoff Are Dangerous

## Short 3 — “Fake health checks”

Use the health check section.

Clip title:

Your App Says Healthy. Users Say Broken.

## Short 4 — “AI changes the bottleneck”

Use the AI-era section.

Clip title:

AI Changed the Software Engineering Bottleneck

---

# Thumbnail Concepts

## Thumbnail Option 1

Text:

WORKS ≠ READY

Visual:

You pointing at a clean AI app diagram on one side and a broken production diagram on the other.

## Thumbnail Option 2

Text:

NOT PROD READY

Visual:

Generated code on screen, red production errors overlaid.

## Thumbnail Option 3

Text:

AI APP FAILED

Visual:

You looking at terminal logs with red error highlights.

Best option:

WORKS ≠ READY

It is simple, broad, and instantly understandable.

---

# Description Draft

AI can generate a working app in minutes. But working is not the same thing as production-ready.

In this video, I show why AI-generated applications often fail basic production-readiness tests: slow dependencies, bad retries, fake health checks, missing timeouts, weak observability, and no recovery path.

This is also the beginning of my new open-source project: High Availability The Hard Way.

The goal: build real systems, break them under realistic production failures, and harden them step by step.

Topics covered:

- Why the happy path is not enough
- Why slow dependencies are dangerous
- How retries can make outages worse
- Why health checks often lie
- What production-readiness actually means
- Why reliability matters even more in the AI coding era

Run Lab 2 after watching:

```bash
git clone https://github.com/isbkch/high-availability-the-hard-way.git
cd high-availability-the-hard-way
cd labs/02-timeouts
make up
make smoke-test
make break
make load-test
make apply-fix
make load-test
```

Repo: [GitHub](https://github.com/isbkch/high-availability-the-hard-way)

---

# Pinned Comment Draft

This is the first video in the High Availability The Hard Way series.

The plan: build a real app, break it under production-style failures, and harden it step by step.

Start here: run Lab 2, the timeout lab.

```bash
git clone https://github.com/isbkch/high-availability-the-hard-way.git
cd high-availability-the-hard-way
cd labs/02-timeouts
make up
make smoke-test
make break
make load-test
make apply-fix
make load-test
```

Repo: [GitHub](https://github.com/isbkch/high-availability-the-hard-way)
