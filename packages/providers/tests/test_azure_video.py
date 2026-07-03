"""AzureVideoEmbedder tests — offline fallback, dimensionality, registry wiring."""

from __future__ import annotations

import pytest
from metavita_providers import AzureVideoEmbedder, default_provider_registry


@pytest.mark.asyncio
async def test_offline_embedding_is_deterministic_and_right_dim():
    emb = AzureVideoEmbedder(dim=1536)  # no key/endpoint → offline fallback
    r1 = await emb.embed(["https://v/clip.mp4"], model="azure-video")
    r2 = await emb.embed(["https://v/clip.mp4"], model="azure-video")
    assert r1.dim == 1536
    assert len(r1.vectors[0]) == 1536
    assert r1.vectors[0] == r2.vectors[0]  # deterministic
    assert all(-1.0 <= x <= 1.0 for x in r1.vectors[0])


@pytest.mark.asyncio
async def test_distinct_videos_get_distinct_vectors():
    emb = AzureVideoEmbedder(dim=64)
    a = (await emb.embed(["https://v/a.mp4"], model="m")).vectors[0]
    b = (await emb.embed(["https://v/b.mp4"], model="m")).vectors[0]
    assert a != b


def test_registered_as_embedding_provider():
    assert "azure_video" in default_provider_registry.embedding_keys()
    inst = default_provider_registry.create_embedding("azure_video", base_url="https://x")
    assert isinstance(inst, AzureVideoEmbedder)
