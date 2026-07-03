"""Video / multimodal embedder factory — build from a `video` Connection.

`build_video_embedder(provider, values, *, dim)` returns an EmbeddingProvider that
vectorizes video URLs. The default (and `azure_video`) is the Azure AI Vision
embedder, which falls back to a deterministic offline embedding when no endpoint /
key is configured — so multimodal ingestion is runnable and testable offline.

Other video providers (AWS Rekognition / GCP Video Intelligence / TwelveLabs) plug
in here as their adapters land; until then they fall back to the Azure embedder.
"""

from __future__ import annotations

from metavita_providers import AzureVideoEmbedder, EmbeddingProvider


def build_video_embedder(
    provider: str | None,
    values: dict | None,
    *,
    dim: int = 1536,
) -> EmbeddingProvider:
    """Construct a video embedder for a workspace.

    - `provider` None / "azure_video" → Azure AI Vision (offline fallback built in).
    - other providers → Azure embedder fallback until a dedicated adapter lands.
    """
    values = values or {}
    # azure_video is the only wired video adapter today; everything routes to it.
    return AzureVideoEmbedder(
        api_key=values.get("api_key"),
        endpoint=values.get("endpoint"),
        dim=dim,
    )
