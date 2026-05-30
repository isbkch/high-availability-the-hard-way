# Reflection

Use these prompts after running the lab.

1. Which endpoint showed the most visible latency before the timeout fix?
2. What happened to worker document processing when LLM latency was injected?
3. After `make apply-fix`, did the system return success, a fast error, or degraded health?
4. What user-facing behavior would you prefer when the LLM is slow: waiting, a fast retryable error, or a fallback answer?
5. Which timeout budget would you tune first in production: connect, read, write, or pool?

The goal is not that every request succeeds under dependency latency. The goal is bounded latency and fast failure so the system can preserve capacity and expose a clear degraded state.
