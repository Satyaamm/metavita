"""Video embedder factory tests — builds a runnable embedder per video connection."""

from __future__ import annotations

import pytest
from metavita_api.services.video import build_video_embedder
from metavita_providers import AzureVideoEmbedder


def test_builds_azure_for_default_and_azure_video():
    for provider in (None, "azure_video"):
        emb = build_video_embedder(provider, {}, dim=1536)
        assert isinstance(emb, AzureVideoEmbedder)


def test_other_providers_fall_back_to_runnable_embedder():
    emb = build_video_embedder("aws_rekognition", {"region": "us-east-1"}, dim=256)
    assert isinstance(emb, AzureVideoEmbedder)


@pytest.mark.asyncio
async def test_embedder_runs_offline_with_correct_dim():
    emb = build_video_embedder("azure_video", {}, dim=128)  # no endpoint/key → offline fallback
    res = await emb.embed(["https://videos.test/clip.mp4"], model="")
    assert res.dim == 128
    assert len(res.vectors[0]) == 128
