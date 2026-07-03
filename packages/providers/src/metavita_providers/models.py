"""Static model registry — capabilities used for routing + cost estimation.

Cached snapshot; the live source of truth is each provider's Models API. Prices
are USD per 1M tokens. Embedding entries carry their output dimension (this drives
the pgvector column width).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChatModel:
    id: str
    provider: str
    context_window: int
    supports_tools: bool
    input_price: float
    output_price: float


@dataclass(frozen=True, slots=True)
class EmbeddingModel:
    id: str
    provider: str
    dim: int
    input_price: float


CHAT_MODELS: dict[str, ChatModel] = {
    "claude-opus-4-8": ChatModel("claude-opus-4-8", "anthropic", 1_000_000, True, 5.0, 25.0),
    "claude-sonnet-4-6": ChatModel("claude-sonnet-4-6", "anthropic", 1_000_000, True, 3.0, 15.0),
    "claude-haiku-4-5": ChatModel("claude-haiku-4-5", "anthropic", 200_000, True, 1.0, 5.0),
    "gpt-4o": ChatModel("gpt-4o", "openai", 128_000, True, 2.5, 10.0),
    "gpt-4o-mini": ChatModel("gpt-4o-mini", "openai", 128_000, True, 0.15, 0.6),
}

EMBEDDING_MODELS: dict[str, EmbeddingModel] = {
    "text-embedding-3-small": EmbeddingModel("text-embedding-3-small", "openai", 1536, 0.02),
    "text-embedding-3-large": EmbeddingModel("text-embedding-3-large", "openai", 3072, 0.13),
    "nomic-embed-text": EmbeddingModel("nomic-embed-text", "ollama", 768, 0.0),
}
