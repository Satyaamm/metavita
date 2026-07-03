"""Ollama local adapter (chat + embeddings). No API key required."""

from __future__ import annotations

import json
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


class OllamaProvider:
    name = "ollama"

    def __init__(self, base_url: str = "http://localhost:11434") -> None:
        self._base_url = base_url.rstrip("/")

    def _to_ollama(
        self, messages: Sequence[ChatMessage], system: str | None
    ) -> list[dict[str, str]]:
        out: list[dict[str, str]] = []
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
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": model,
                    "messages": self._to_ollama(messages, system),
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return ChatResult(
            text=data["message"]["content"],
            model=model,
            usage=Usage(
                data.get("prompt_eval_count", 0), data.get("eval_count", 0)
            ),
            stop_reason=data.get("done_reason"),
        )

    async def chat_stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        async with httpx.AsyncClient(timeout=120) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/api/chat",
                json={
                    "model": model,
                    "messages": self._to_ollama(messages, system),
                    "stream": True,
                    "options": {"num_predict": max_tokens},
                },
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    chunk = data.get("message", {}).get("content")
                    if chunk:
                        yield chunk

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
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self._base_url}/api/embed",
                json={"model": model, "input": list(texts)},
            )
            resp.raise_for_status()
            data = resp.json()
        vectors = data["embeddings"]
        return EmbeddingResult(
            vectors=vectors,
            model=model,
            dim=len(vectors[0]) if vectors else 0,
        )
