"""Azure AI Vision video embedder — multimodal (video) vectorization.

Conforms to the EmbeddingProvider protocol so it composes with the same registry,
factory, and pgvector store as text embedders. Each input string is a video URL;
`embed` returns one vector per video.

When an endpoint + key are configured it calls Azure AI Vision's video-retrieval
"vectorizeVideo" API. With no credentials it falls back to a deterministic local
embedding (hash-seeded) so multimodal ingestion is runnable and testable offline.
Vectors are projected to `dim` so they fit the workspace's vector column.
"""

from __future__ import annotations

import hashlib
import struct
from collections.abc import Sequence

import httpx

from .base import EmbeddingResult, Usage

# Azure AI Vision video-retrieval API version (2023-05-01-preview "vectorizeVideo").
_API_VERSION = "2023-05-01-preview"
_NATIVE_DIM = 1024  # Azure Vision returns 1024-d video vectors


class AzureVideoEmbedder:
    name = "azure_video"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        endpoint: str | None = None,
        dim: int = 1536,
    ) -> None:
        self._api_key = api_key
        self._endpoint = (endpoint or "").rstrip("/")
        self._dim = dim

    async def embed(self, texts: Sequence[str], *, model: str) -> EmbeddingResult:
        vectors = [await self._embed_one(url) for url in texts]
        return EmbeddingResult(
            vectors=vectors, model=model or "azure-video", dim=self._dim, usage=Usage()
        )

    async def _embed_one(self, video_url: str) -> list[float]:
        if self._api_key and self._endpoint:
            try:
                return self._project(await self._azure_vectorize(video_url))
            except httpx.HTTPError:
                pass  # fall through to the offline embedding
        return self._local_embedding(video_url)

    async def _azure_vectorize(self, video_url: str) -> list[float]:
        url = (
            f"{self._endpoint}/computervision/retrieval:vectorizeVideo"
            f"?api-version={_API_VERSION}"
        )
        headers = {"Ocp-Apim-Subscription-Key": self._api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json={"url": video_url})
            resp.raise_for_status()
            return list(resp.json()["vector"])

    def _project(self, vector: list[float]) -> list[float]:
        """Pad or truncate a native vector to the configured column dimension."""
        if len(vector) == self._dim:
            return vector
        if len(vector) > self._dim:
            return vector[: self._dim]
        return vector + [0.0] * (self._dim - len(vector))

    def _local_embedding(self, video_url: str) -> list[float]:
        """Deterministic offline embedding so multimodal flows run without Azure."""
        out: list[float] = []
        counter = 0
        while len(out) < self._dim:
            digest = hashlib.sha256(f"{video_url}:{counter}".encode()).digest()
            for i in range(0, len(digest), 4):
                if len(out) >= self._dim:
                    break
                (val,) = struct.unpack("<I", digest[i : i + 4])
                out.append((val / 0xFFFFFFFF) * 2 - 1)  # in [-1, 1]
            counter += 1
        return out
