"""Anthropic (Claude) chat adapter.

Note: Anthropic exposes no embeddings endpoint — this provider implements
ChatProvider only. Embeddings are served by OpenAI/Ollama (see registry).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from anthropic import AsyncAnthropic

from .base import (
    AgentMessage,
    ChatMessage,
    ChatResult,
    ToolCall,
    ToolDef,
    ToolTurn,
    Usage,
)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str | None = None) -> None:
        # AsyncAnthropic resolves ANTHROPIC_API_KEY from the env when api_key is None.
        self._client = AsyncAnthropic(api_key=api_key) if api_key else AsyncAnthropic()

    def _split(
        self, messages: Sequence[ChatMessage], system: str | None
    ) -> tuple[str | None, list[dict[str, str]]]:
        systems = [m.content for m in messages if m.role == "system"]
        if system:
            systems.insert(0, system)
        turns = [
            {"role": m.role, "content": m.content}
            for m in messages
            if m.role != "system"
        ]
        combined_system = "\n\n".join(systems) if systems else None
        return combined_system, turns

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> ChatResult:
        combined_system, turns = self._split(messages, system)
        kwargs: dict = {"model": model, "max_tokens": max_tokens, "messages": turns}
        if combined_system:
            kwargs["system"] = combined_system
        resp = await self._client.messages.create(**kwargs)
        text = "".join(b.text for b in resp.content if b.type == "text")
        return ChatResult(
            text=text,
            model=resp.model,
            usage=Usage(resp.usage.input_tokens, resp.usage.output_tokens),
            stop_reason=resp.stop_reason,
        )

    async def chat_stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        combined_system, turns = self._split(messages, system)
        kwargs: dict = {"model": model, "max_tokens": max_tokens, "messages": turns}
        if combined_system:
            kwargs["system"] = combined_system
        async with self._client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    @staticmethod
    def _agent_message(m: AgentMessage) -> dict:
        if m.tool_results:
            return {
                "role": "user",
                "content": [
                    {"type": "tool_result", "tool_use_id": tr.tool_use_id, "content": tr.content}
                    for tr in m.tool_results
                ],
            }
        if m.tool_calls:
            content: list[dict] = []
            if m.text:
                content.append({"type": "text", "text": m.text})
            content.extend(
                {"type": "tool_use", "id": tc.id, "name": tc.name, "input": tc.input}
                for tc in m.tool_calls
            )
            return {"role": "assistant", "content": content}
        return {"role": m.role, "content": m.text or ""}

    async def chat_tools(
        self,
        messages: Sequence[AgentMessage],
        *,
        model: str,
        tools: Sequence[ToolDef],
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> ToolTurn:
        kwargs: dict = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [self._agent_message(m) for m in messages],
            "tools": [
                {"name": t.name, "description": t.description, "input_schema": t.input_schema}
                for t in tools
            ],
        }
        if system:
            kwargs["system"] = system
        resp = await self._client.messages.create(**kwargs)
        text = "".join(b.text for b in resp.content if b.type == "text")
        tool_calls = [
            ToolCall(id=b.id, name=b.name, input=dict(b.input))
            for b in resp.content
            if b.type == "tool_use"
        ]
        return ToolTurn(
            text=text,
            tool_calls=tool_calls,
            stop_reason=resp.stop_reason,
            usage=Usage(resp.usage.input_tokens, resp.usage.output_tokens),
        )
