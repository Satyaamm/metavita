"""Object storage tests — LocalObjectStore round-trip + key namespacing."""

from __future__ import annotations

import pytest
from metavita_api.storage import LocalObjectStore, object_key


def test_object_key_is_workspace_namespaced():
    assert object_key("ws-1", "doc/file.pdf") == "ws-1/doc/file.pdf"


@pytest.mark.asyncio
async def test_local_store_round_trip(tmp_path):
    store = LocalObjectStore(tmp_path)
    key = object_key("ws-1", "abc/report.txt")
    uri = await store.put(key, b"hello bytes", content_type="text/plain")
    assert uri.startswith("file://")
    assert await store.get(key) == b"hello bytes"


@pytest.mark.asyncio
async def test_local_store_overwrite(tmp_path):
    store = LocalObjectStore(tmp_path)
    await store.put("k", b"one")
    await store.put("k", b"two")
    assert await store.get("k") == b"two"
