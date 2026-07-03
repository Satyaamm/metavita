"""Provider registry — maps a provider key to an adapter builder.

Registry pattern: register `key -> builder` once; `create_*` looks up the builder,
enforces the per-workspace `allowed` policy (HIPAA/BAA gating), and returns a
configured adapter instance. The API's ProviderFactory composes this with settings
and credentials. New providers are added by registering a builder — no call-site edits.
"""

from __future__ import annotations

from collections.abc import Callable

from .anthropic_provider import AnthropicProvider
from .azure_video_provider import AzureVideoEmbedder
from .base import ChatProvider, EmbeddingProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider

ChatBuilder = Callable[..., ChatProvider]
EmbeddingBuilder = Callable[..., EmbeddingProvider]


class ProviderError(RuntimeError):
    """Raised on unknown providers or policy violations."""


# --- Adapter builders (key -> configured instance) --------------------------
def _build_anthropic(api_key: str | None = None, base_url: str | None = None) -> ChatProvider:
    return AnthropicProvider(api_key=api_key)


def _build_openai(api_key: str | None = None, base_url: str | None = None) -> OpenAIProvider:
    return OpenAIProvider(api_key=api_key, base_url=base_url)


def _build_ollama(api_key: str | None = None, base_url: str | None = None) -> OllamaProvider:
    return OllamaProvider(base_url=base_url or "http://localhost:11434")


def _build_azure_video(
    api_key: str | None = None, base_url: str | None = None
) -> AzureVideoEmbedder:
    # `base_url` carries the Azure AI Vision endpoint for this provider.
    return AzureVideoEmbedder(api_key=api_key, endpoint=base_url)


class ProviderRegistry:
    """Holds chat/embedding builders keyed by provider name."""

    def __init__(self) -> None:
        self._chat: dict[str, ChatBuilder] = {}
        self._embedding: dict[str, EmbeddingBuilder] = {}

    # registration -----------------------------------------------------------
    def register_chat(self, name: str, builder: ChatBuilder) -> None:
        self._chat[name] = builder

    def register_embedding(self, name: str, builder: EmbeddingBuilder) -> None:
        self._embedding[name] = builder

    def chat_keys(self) -> list[str]:
        return sorted(self._chat)

    def embedding_keys(self) -> list[str]:
        return sorted(self._embedding)

    # construction -----------------------------------------------------------
    @staticmethod
    def _guard(name: str, allowed: set[str] | None) -> None:
        if allowed is not None and name not in allowed:
            raise ProviderError(
                f"provider '{name}' not permitted for this workspace "
                f"(allowed: {sorted(allowed)})"
            )

    def create_chat(
        self,
        name: str,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        allowed: set[str] | None = None,
    ) -> ChatProvider:
        self._guard(name, allowed)
        builder = self._chat.get(name)
        if builder is None:
            raise ProviderError(f"unknown chat provider: {name}")
        return builder(api_key=api_key, base_url=base_url)

    def create_embedding(
        self,
        name: str,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        allowed: set[str] | None = None,
    ) -> EmbeddingProvider:
        self._guard(name, allowed)
        builder = self._embedding.get(name)
        if builder is None:
            if name == "anthropic":
                raise ProviderError(
                    "Anthropic provides no embeddings API; use openai or ollama for embeddings"
                )
            raise ProviderError(f"unknown embedding provider: {name}")
        return builder(api_key=api_key, base_url=base_url)


def _default_registry() -> ProviderRegistry:
    reg = ProviderRegistry()
    # Chat
    reg.register_chat("anthropic", _build_anthropic)
    reg.register_chat("openai", _build_openai)
    reg.register_chat("byo", _build_openai)
    reg.register_chat("ollama", _build_ollama)
    # Embeddings (Anthropic intentionally absent — no embeddings API)
    reg.register_embedding("openai", _build_openai)
    reg.register_embedding("byo", _build_openai)
    reg.register_embedding("ollama", _build_ollama)
    reg.register_embedding("azure_video", _build_azure_video)  # multimodal / video
    return reg


#: Process-wide default registry; the API factory uses this unless overridden.
default_provider_registry = _default_registry()
