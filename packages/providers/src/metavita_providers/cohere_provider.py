"""Cohere adapter — chat + embeddings via the Cohere v2 REST API.

Brought by the user as a `cohere` Connection (api_key + model). Streaming and
tool-use degrade to a single text turn (parity with the Ollama/OpenAI fallbacks).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

import httpx

from .base import (
    AgentMessage,
    ChatMessage,
    ChatResult,
    EmbeddingResult,
    ToolDef,
    ToolTurn,
    Usage,
)

_BASE = "https://api.cohere.com"


class CohereProvider:
    name = "cohere"

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        self._api_key = api_key or ""
        self._base = (base_url or _BASE).rstrip("/")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _messages(messages: Sequence[ChatMessage], system: str | None) -> list[dict]:
        out: list[dict] = []
        if system:
            out.append({"role": "system", "content": system})
        out.extend({"role": m.role, "content": m.content} for m in messages)
        return out

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> ChatResult:
        body = {
            "model": model,
            "messages": self._messages(messages, system),
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self._base}/v2/chat", headers=self._headers(), json=body)
            resp.raise_for_status()
            data = resp.json()
        parts = data.get("message", {}).get("content", [])
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        tokens = (data.get("usage", {}) or {}).get("tokens", {}) or {}
        return ChatResult(
            text=text,
            model=model,
            usage=Usage(int(tokens.get("input_tokens", 0)), int(tokens.get("output_tokens", 0))),
            stop_reason=data.get("finish_reason"),
        )

    async def chat_stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        res = await self.chat(messages, model=model, max_tokens=max_tokens, system=system)
        if res.text:
            yield res.text

    async def chat_tools(
        self,
        messages: Sequence[AgentMessage],
        *,
        model: str,
        tools: Sequence[ToolDef],
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> ToolTurn:
        flat = [ChatMessage(m.role, m.text or "") for m in messages if m.text]
        res = await self.chat(flat, model=model, max_tokens=max_tokens, system=system)
        return ToolTurn(text=res.text, tool_calls=[], stop_reason=res.stop_reason, usage=res.usage)

    async def embed(self, texts: Sequence[str], *, model: str) -> EmbeddingResult:
        body = {
            "model": model,
            "texts": list(texts),
            "input_type": "search_document",
            "embedding_types": ["float"],
        }
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{self._base}/v2/embed", headers=self._headers(), json=body)
            resp.raise_for_status()
            data = resp.json()
        vectors = (data.get("embeddings", {}) or {}).get("float", [])
        return EmbeddingResult(
            vectors=vectors, model=model, dim=len(vectors[0]) if vectors else 0
        )
