"""OpenAI chat + embedding adapter (also serves OpenAI-compatible BYO endpoints)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from openai import AsyncOpenAI

from .base import (
    AgentMessage,
    ChatMessage,
    ChatResult,
    EmbeddingResult,
    ToolDef,
    ToolTurn,
    Usage,
)


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str | None = None, base_url: str | None = None) -> None:
        # base_url lets this same adapter target any OpenAI-compatible endpoint (BYO).
        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    def _to_openai(
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
        resp = await self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=self._to_openai(messages, system),
        )
        choice = resp.choices[0]
        usage = resp.usage
        return ChatResult(
            text=choice.message.content or "",
            model=resp.model,
            usage=Usage(
                usage.prompt_tokens if usage else 0,
                usage.completion_tokens if usage else 0,
            ),
            stop_reason=choice.finish_reason,
        )

    async def chat_stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        stream = await self._client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=self._to_openai(messages, system),
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    async def chat_tools(
        self,
        messages: Sequence[AgentMessage],
        *,
        model: str,
        tools: Sequence[ToolDef],
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> ToolTurn:
        # Tool calling not yet wired for this provider — answer from conversation text.
        flat = [ChatMessage(m.role, m.text or "") for m in messages if m.text]
        res = await self.chat(flat, model=model, max_tokens=max_tokens, system=system)
        return ToolTurn(text=res.text, tool_calls=[], stop_reason=res.stop_reason, usage=res.usage)

    async def embed(self, texts: Sequence[str], *, model: str) -> EmbeddingResult:
        resp = await self._client.embeddings.create(model=model, input=list(texts))
        vectors = [d.embedding for d in resp.data]
        return EmbeddingResult(
            vectors=vectors,
            model=resp.model,
            dim=len(vectors[0]) if vectors else 0,
            usage=Usage(resp.usage.prompt_tokens, 0),
        )
