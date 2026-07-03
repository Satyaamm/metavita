"""Object storage — raw document bytes live here, not in Postgres.

Port/adapter: the `ObjectStore` Protocol is implemented by `MinioObjectStore`
(S3/MinIO, prod + self-host) and `LocalObjectStore` (filesystem, dev/tests).
`build_object_store` picks MinIO when an endpoint is configured and reachable,
else falls back to local so ingestion always has somewhere to put bytes.

Keys are namespaced per workspace (`{workspace_id}/{name}`) for tenant isolation.
"""

from __future__ import annotations

import asyncio
import io
from pathlib import Path
from typing import Protocol

from .config import Settings


class ObjectStore(Protocol):
    async def put(self, key: str, data: bytes, *, content_type: str | None = None) -> str: ...
    async def get(self, key: str) -> bytes: ...


def object_key(workspace_id: str, name: str) -> str:
    return f"{workspace_id}/{name}"


class LocalObjectStore:
    """Filesystem-backed store — used in dev/tests and as the MinIO fallback."""

    def __init__(self, root: str | Path) -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        path = self._root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    async def put(self, key: str, data: bytes, *, content_type: str | None = None) -> str:
        path = self._path(key)
        await asyncio.to_thread(path.write_bytes, data)
        return f"file://{path}"

    async def get(self, key: str) -> bytes:
        return await asyncio.to_thread(self._path(key).read_bytes)


class MinioObjectStore:
    """S3/MinIO-backed store. minio client calls are sync → run off the event loop."""

    def __init__(self, settings: Settings) -> None:
        from minio import Minio

        endpoint = settings.s3_endpoint_url.replace("https://", "").replace("http://", "")
        secure = settings.s3_endpoint_url.startswith("https://")
        self._bucket = settings.s3_bucket
        self._client = Minio(
            endpoint,
            access_key=settings.s3_access_key,
            secret_key=settings.s3_secret_key,
            secure=secure,
        )

    def _ensure_bucket(self) -> None:
        if not self._client.bucket_exists(self._bucket):
            self._client.make_bucket(self._bucket)

    async def put(self, key: str, data: bytes, *, content_type: str | None = None) -> str:
        def _put() -> str:
            self._ensure_bucket()
            self._client.put_object(
                self._bucket,
                key,
                io.BytesIO(data),
                length=len(data),
                content_type=content_type or "application/octet-stream",
            )
            return f"s3://{self._bucket}/{key}"

        return await asyncio.to_thread(_put)

    async def get(self, key: str) -> bytes:
        def _get() -> bytes:
            resp = self._client.get_object(self._bucket, key)
            try:
                return resp.read()
            finally:
                resp.close()
                resp.release_conn()

        return await asyncio.to_thread(_get)


def build_object_store(settings: Settings) -> ObjectStore:
    """MinIO when reachable, else a local filesystem store (dev convenience)."""
    if settings.s3_endpoint_url:
        try:
            store = MinioObjectStore(settings)
            # Probe connectivity so we degrade cleanly when MinIO isn't running.
            store._client.bucket_exists(store._bucket)
            return store
        except Exception:  # noqa: BLE001 - any connectivity/SDK error → local fallback
            pass
    return LocalObjectStore(Path(settings.local_object_root))
