"""Provider-agnostic interfaces for chat and embeddings.

Chat (reasoning/agent nodes) and embeddings are deliberately separate protocols:
Anthropic provides chat but no embeddings API, while OpenAI/Ollama provide both.
The registry wires a concrete chat provider and embedding provider per workspace.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass, field
from typing import Literal, Protocol, runtime_checkable

Role = Literal["system", "user", "assistant"]


@dataclass(slots=True)
class ChatMessage:
    role: Role
    content: str


@dataclass(slots=True)
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0


@dataclass(slots=True)
class ChatResult:
    text: str
    model: str
    usage: Usage = field(default_factory=Usage)
    stop_reason: str | None = None


@dataclass(slots=True)
class EmbeddingResult:
    vectors: list[list[float]]
    model: str
    dim: int
    usage: Usage = field(default_factory=Usage)


# --- Tool use (agent loop) --------------------------------------------------
@dataclass(slots=True)
class ToolDef:
    name: str
    description: str
    input_schema: dict


@dataclass(slots=True)
class ToolCall:
    id: str
    name: str
    input: dict


@dataclass(slots=True)
class ToolResult:
    tool_use_id: str
    content: str


@dataclass(slots=True)
class AgentMessage:
    role: Role  # "user" | "assistant"
    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[ToolResult] = field(default_factory=list)


@dataclass(slots=True)
class ToolTurn:
    text: str
    tool_calls: list[ToolCall]
    stop_reason: str | None = None
    usage: Usage = field(default_factory=Usage)


@runtime_checkable
class ChatProvider(Protocol):
    """A provider capable of generating chat completions."""

    name: str

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> ChatResult: ...

    def chat_stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        """Yield text deltas as they arrive."""
        ...

    async def chat_tools(
        self,
        messages: Sequence[AgentMessage],
        *,
        model: str,
        tools: Sequence[ToolDef],
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> ToolTurn:
        """One agent turn: returns text and/or tool calls the model wants to make."""
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """A provider capable of generating text embeddings."""

    name: str

    async def embed(
        self, texts: Sequence[str], *, model: str
    ) -> EmbeddingResult: ...
