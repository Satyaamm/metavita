"""Connection resolver — turn a workspace's BYO Connection into a live provider.

Pure-BYO core: a workspace brings its own LLM / embeddings via a `Connection`
(stored encrypted). This module loads the default connection for a capability,
decrypts its values ({**config, **secrets}), and builds the matching provider
adapter. It reuses the shared `metavita_providers` registry for the native
adapters (anthropic / openai / ollama) and maps every OpenAI-compatible vendor
(azure_openai / openai_compatible / mistral / groq / together / openrouter) onto
a single `OpenAIProvider` configured with the connection's base_url + api_key.

The factory composes this with the platform env-key fallback (dev only).
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass

from metavita_providers import (
    BedrockProvider,
    ChatProvider,
    CohereProvider,
    EmbeddingProvider,
    ProviderRegistry,
    VertexProvider,
    default_provider_registry,
)
from metavita_providers.openai_provider import OpenAIProvider
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Connection
from ..repositories import ConnectionRepository
from ..security.encryption import get_secret_box

# Providers we route straight onto the OpenAIProvider adapter (OpenAI-compatible
# REST surface). Each connection supplies its own base_url + api_key + model.
_OPENAI_COMPATIBLE: frozenset[str] = frozenset(
    {"openai", "azure_openai", "openai_compatible", "mistral", "groq", "together", "openrouter"}
)

# Default base URLs for vendors whose connection form omits an explicit base_url.
_DEFAULT_BASE_URL: dict[str, str] = {
    "mistral": "https://api.mistral.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
    "together": "https://api.together.xyz/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "openai": "https://api.openai.com/v1",
}


@dataclass(slots=True)
class ResolvedChat:
    provider: ChatProvider
    model: str


@dataclass(slots=True)
class ResolvedEmbedding:
    provider: EmbeddingProvider
    model: str


def connection_values(conn: Connection) -> dict:
    """Decrypt and merge a connection into a flat {**config, **secrets} dict."""
    values: dict = dict(conn.config or {})
    if conn.secret_ciphertext:
        try:
            secrets = json.loads(get_secret_box().decrypt(conn.secret_ciphertext))
        except Exception:  # noqa: BLE001 - corrupt/rotated key → treat as no secrets
            secrets = {}
        values.update(secrets)
    return values


def _azure_base_url(values: dict) -> str | None:
    """Build an OpenAI-compatible base URL for an Azure OpenAI deployment."""
    endpoint = (values.get("endpoint") or "").rstrip("/")
    deployment = values.get("deployment") or values.get("model") or ""
    if not endpoint:
        return None
    # Azure exposes an OpenAI-compatible surface under /openai/deployments/<name>.
    return f"{endpoint}/openai/deployments/{deployment}"


def _base_url_for(provider: str, values: dict) -> str | None:
    if provider == "azure_openai":
        return _azure_base_url(values)
    return values.get("base_url") or _DEFAULT_BASE_URL.get(provider)


def _model_for(provider: str, values: dict, fallback: str) -> str:
    if provider == "azure_openai":
        return values.get("deployment") or values.get("model") or fallback
    return values.get("model") or fallback


def build_chat_from_connection(
    conn: Connection,
    *,
    registry: ProviderRegistry = default_provider_registry,
    default_model: str,
) -> ResolvedChat:
    """Construct a ChatProvider + model from a `llm` connection."""
    provider = conn.provider
    values = connection_values(conn)
    model = _model_for(provider, values, default_model)

    if provider in ("anthropic", "ollama"):
        instance = registry.create_chat(
            provider,
            api_key=values.get("api_key"),
            base_url=values.get("base_url"),
        )
        return ResolvedChat(instance, model)

    if provider in _OPENAI_COMPATIBLE:
        instance = OpenAIProvider(
            api_key=values.get("api_key"),
            base_url=_base_url_for(provider, values),
        )
        return ResolvedChat(instance, model)

    if provider == "cohere":
        return ResolvedChat(
            CohereProvider(api_key=values.get("api_key"), base_url=values.get("base_url")), model
        )

    if provider == "aws_bedrock":
        return ResolvedChat(
            BedrockProvider(
                region=values.get("region", "us-east-1"),
                access_key_id=values.get("access_key_id", ""),
                secret_access_key=values.get("secret_access_key", ""),
                session_token=values.get("session_token"),
            ),
            model,
        )

    if provider == "gcp_vertex":
        return ResolvedChat(
            VertexProvider(
                project_id=values.get("project_id", ""),
                location=values.get("location", "us-central1"),
                service_account_json=values.get("service_account_json", ""),
            ),
            model,
        )

    # Unknown / not-yet-supported provider → let the registry decide (raises clearly).
    instance = registry.create_chat(
        provider, api_key=values.get("api_key"), base_url=values.get("base_url")
    )
    return ResolvedChat(instance, model)


def build_embedding_from_connection(
    conn: Connection,
    *,
    registry: ProviderRegistry = default_provider_registry,
    default_model: str,
) -> ResolvedEmbedding:
    """Construct an EmbeddingProvider + model from an `embeddings` connection."""
    provider = conn.provider
    values = connection_values(conn)
    model = _model_for(provider, values, default_model)

    if provider == "ollama":
        instance = registry.create_embedding(
            "ollama", api_key=None, base_url=values.get("base_url")
        )
        return ResolvedEmbedding(instance, model)

    if provider in _OPENAI_COMPATIBLE:
        instance = OpenAIProvider(
            api_key=values.get("api_key"),
            base_url=_base_url_for(provider, values),
        )
        return ResolvedEmbedding(instance, model)

    if provider == "cohere":
        return ResolvedEmbedding(
            CohereProvider(api_key=values.get("api_key"), base_url=values.get("base_url")), model
        )

    # voyage / jina and friends are not yet wired as embedding adapters;
    # surface a clear error rather than silently mis-embedding.
    instance = registry.create_embedding(
        provider, api_key=values.get("api_key"), base_url=values.get("base_url")
    )
    return ResolvedEmbedding(instance, model)


async def default_connection(
    session: AsyncSession,
    workspace_id: uuid.UUID,
    capability: str,
) -> Connection | None:
    """The default connection for a capability: the most recently created one.

    `ConnectionRepository.list` already orders by created_at desc, so the first
    entry is the workspace's effective default for that capability.
    """
    conns = await ConnectionRepository(session).list(workspace_id, capability=capability)
    return conns[0] if conns else None
