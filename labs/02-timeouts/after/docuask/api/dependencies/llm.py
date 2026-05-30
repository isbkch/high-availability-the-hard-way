"""OpenAI-compatible LLM client dependencies with explicit timeout budgets."""

from __future__ import annotations

import httpx

from docuask.config import Settings, get_settings


LLM_TIMEOUT = httpx.Timeout(
    connect=1.0,
    read=2.0,
    write=1.0,
    pool=0.5,
)
LLM_HEALTH_TIMEOUT = httpx.Timeout(
    connect=0.5,
    read=1.0,
    write=0.5,
    pool=0.5,
)


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

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Create embeddings for one or more text inputs."""
        payload = {
            "model": "text-embedding-3-small",
            "input": texts,
        }
        try:
            async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
                response = await client.post(
                    self._url("/embeddings"),
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RuntimeError("LLM embeddings timed out") from exc
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
        try:
            async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
                response = await client.post(
                    self._url("/chat/completions"),
                    headers=self._headers(),
                    json=payload,
                )
                response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise RuntimeError("LLM chat completion timed out") from exc
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
