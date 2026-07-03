"""MetaVita Python SDK tests — auth routing + response parsing (mocked HTTP)."""

from __future__ import annotations

import httpx
import pytest
from metavita import AnswerResponse, MetaVita, MetaVitaError


def _client(handler) -> MetaVita:
    return MetaVita(
        "https://api.test",
        api_key="mv_key",
        token="jwt",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


@pytest.mark.asyncio
async def test_serve_uses_deployment_key():
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["auth"] = req.headers.get("authorization")
        seen["url"] = str(req.url)
        return httpx.Response(200, json={"answer": "hi", "citations": [], "run_id": "r1"})

    async with _client(handler) as mv:
        res = await mv.serve("dep-1", question="hello")
    assert isinstance(res, AnswerResponse)
    assert res.answer == "hi" and res.run_id == "r1"
    assert seen["auth"] == "Bearer mv_key"
    assert seen["url"].endswith("/serve/dep-1")


@pytest.mark.asyncio
async def test_query_uses_token_not_key():
    seen = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen["auth"] = req.headers.get("authorization")
        cite = {"marker": 1, "document_id": "d", "chunk_index": 0, "snippet": "s"}
        return httpx.Response(200, json={"answer": "a", "citations": [cite]})

    async with _client(handler) as mv:
        res = await mv.query(question="q")
    assert seen["auth"] == "Bearer jwt"
    assert res.citations[0].marker == 1


@pytest.mark.asyncio
async def test_error_raises():
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(401, text="nope")

    async with _client(handler) as mv:
        with pytest.raises(MetaVitaError) as ei:
            await mv.serve("d", question="x")
    assert ei.value.status == 401
