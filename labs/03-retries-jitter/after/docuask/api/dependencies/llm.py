"""OpenAI-compatible LLM client with bounded backoff and jitter."""

from __future__ import annotations

import asyncio
import random

import httpx

from docuask.config import Settings, get_settings


MAX_RETRY_ATTEMPTS = 4
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Retry budget: each LLM call gets at most four attempts, a two-second read
# timeout per attempt, and short exponential backoff with jitter between tries.
LLM_TIMEOUT = httpx.Timeout(connect=1.0, read=2.0, write=1.0, pool=0.5)
LLM_HEALTH_TIMEOUT = httpx.Timeout(connect=0.5, read=1.0, write=0.5, pool=0.5)
RETRY_BASE_DELAY_SECONDS = 0.15
RETRY_MAX_DELAY_SECONDS = 1.2
RETRY_JITTER_SECONDS = 0.25


class LLMClient:
    """Small OpenAI-compatible client for embeddings and chat completions."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        return f"{self.settings.llm_api_base.rstrip('/')}/{path.lstrip('/')}"

    def _retry_delay(self, attempt: int) -> float:
        backoff = min(
            RETRY_MAX_DELAY_SECONDS,
            RETRY_BASE_DELAY_SECONDS * (2 ** (attempt - 1)),
        )
        return backoff + random.uniform(0.0, RETRY_JITTER_SECONDS)

    async def _post_with_backoff(self, path: str, payload: dict) -> httpx.Response:
        last_response: httpx.Response | None = None
        last_error: Exception | None = None
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
                try:
                    response = await client.post(
                        self._url(path),
                        headers=self._headers(),
                        json=payload,
                    )
                    if response.status_code not in RETRYABLE_STATUS_CODES:
                        response.raise_for_status()
                        return response
                    last_response = response
                except (httpx.TimeoutException, httpx.TransportError) as exc:
                    last_error = exc

                if attempt == MAX_RETRY_ATTEMPTS:
                    break
                delay = self._retry_delay(attempt)
                await asyncio.sleep(delay)

        if last_response is not None:
            last_response.raise_for_status()
        raise RuntimeError(
            f"LLM request failed after retry budget of {MAX_RETRY_ATTEMPTS} attempts"
        ) from last_error

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for one or more text inputs."""
        payload = {
            "model": "text-embedding-3-small",
            "input": texts,
        }
        response = await self._post_with_backoff("/embeddings", payload)
        data = response.json()
        return [item["embedding"] for item in data.get("data", [])]

    async def answer_question(self, question: str, contexts: list[str]) -> str:
        """Answer a question using retrieved document context."""
        context = "\n\n".join(contexts) or "No relevant document chunks were found."
        payload = {
            "model": self.settings.llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Answer using only the supplied document context. "
                        "If the context is insufficient, say so briefly."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {question}",
                },
            ],
        }
        response = await self._post_with_backoff("/chat/completions", payload)
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")

    async def health(self) -> str:
        """Return health status for the configured LLM endpoint."""
        try:
            async with httpx.AsyncClient(timeout=LLM_HEALTH_TIMEOUT) as client:
                response = await client.get(self._url("/models"), headers=self._headers())
            return "healthy" if 200 <= response.status_code < 400 else "unhealthy"
        except Exception:
            return "unhealthy"


async def get_llm_client() -> LLMClient:
    """FastAPI dependency for the LLM client."""
    return LLMClient()


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Worker helper for embeddings."""
    return await LLMClient().embed_texts(texts)
