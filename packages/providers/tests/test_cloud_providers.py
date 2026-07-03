"""Tests for the BYO cloud adapters — Cohere, Bedrock (SigV4), Vertex.

HTTP is faked by swapping each module's httpx.AsyncClient, so request shaping and
response parsing are verified offline (no live cloud accounts).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from metavita_providers import bedrock_provider, cohere_provider, vertex_provider
from metavita_providers._awssig import sigv4_headers
from metavita_providers.base import ChatMessage


class _Resp:
    def __init__(self, data):
        self._d = data

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


class _Client:
    def __init__(self, data, capture):
        self._d = data
        self._cap = capture

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    async def post(self, url, **kw):
        self._cap.append((url, kw))
        return _Resp(self._d)


def _patch(monkeypatch, module, data, capture):
    monkeypatch.setattr(module.httpx, "AsyncClient", lambda *a, **k: _Client(data, capture))


# --- SigV4 ---------------------------------------------------------------------
def test_sigv4_is_deterministic_and_well_formed():
    fixed = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)
    h = sigv4_headers(
        method="POST", host="bedrock-runtime.us-east-1.amazonaws.com",
        path="/model/m/invoke", region="us-east-1", service="bedrock",
        payload=b'{"x":1}', access_key="AKIA", secret_key="secret", now=fixed,
    )
    assert h["Authorization"].startswith(
        "AWS4-HMAC-SHA256 Credential=AKIA/20260102/us-east-1/bedrock/"
    )
    assert "SignedHeaders=content-type;host;x-amz-content-sha256;x-amz-date" in h["Authorization"]
    assert "Signature=" in h["Authorization"] and h["X-Amz-Date"] == "20260102T030405Z"
    # determinism
    h2 = sigv4_headers(
        method="POST", host="bedrock-runtime.us-east-1.amazonaws.com",
        path="/model/m/invoke", region="us-east-1", service="bedrock",
        payload=b'{"x":1}', access_key="AKIA", secret_key="secret", now=fixed,
    )
    assert h == h2


# --- Cohere --------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cohere_chat(monkeypatch):
    cap = []
    _patch(monkeypatch, cohere_provider,
           {"message": {"content": [{"type": "text", "text": "hi"}]},
            "usage": {"tokens": {"input_tokens": 5, "output_tokens": 2}}}, cap)
    p = cohere_provider.CohereProvider(api_key="k")
    res = await p.chat([ChatMessage("user", "yo")], model="command-r", system="sys")
    assert res.text == "hi" and res.usage.input_tokens == 5
    body = cap[-1][1]["json"]
    assert body["messages"][0] == {"role": "system", "content": "sys"}


@pytest.mark.asyncio
async def test_cohere_embed(monkeypatch):
    cap = []
    _patch(monkeypatch, cohere_provider, {"embeddings": {"float": [[0.1, 0.2, 0.3]]}}, cap)
    p = cohere_provider.CohereProvider(api_key="k")
    res = await p.embed(["a"], model="embed-english-v3.0")
    assert res.vectors == [[0.1, 0.2, 0.3]] and res.dim == 3


# --- Bedrock -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_bedrock_chat_signs_and_parses(monkeypatch):
    cap = []
    _patch(monkeypatch, bedrock_provider,
           {"content": [{"type": "text", "text": "b"}],
            "usage": {"input_tokens": 3, "output_tokens": 1}}, cap)
    p = bedrock_provider.BedrockProvider(
        region="us-east-1", access_key_id="AKIA", secret_access_key="s"
    )
    res = await p.chat([ChatMessage("user", "q")], model="anthropic.claude-3-5-sonnet", system="s")
    assert res.text == "b" and res.usage.output_tokens == 1
    headers = cap[-1][1]["headers"]
    assert headers["Authorization"].startswith("AWS4-HMAC-SHA256")


# --- Vertex --------------------------------------------------------------------
@pytest.mark.asyncio
async def test_vertex_chat(monkeypatch):
    cap = []
    _patch(monkeypatch, vertex_provider,
           {"candidates": [{"content": {"parts": [{"text": "v"}]}, "finishReason": "STOP"}],
            "usageMetadata": {"promptTokenCount": 4, "candidatesTokenCount": 1}}, cap)
    p = vertex_provider.VertexProvider(
        project_id="proj", location="us-central1", service_account_json={}
    )

    async def _tok():
        return "tok"

    monkeypatch.setattr(p, "_access_token", _tok)
    res = await p.chat([ChatMessage("user", "hi")], model="gemini-1.5-pro", system="s")
    assert res.text == "v" and res.usage.input_tokens == 4
    url, kw = cap[-1]
    assert "gemini-1.5-pro:generateContent" in url
    assert kw["headers"]["Authorization"] == "Bearer tok"
    assert kw["json"]["systemInstruction"]["parts"][0]["text"] == "s"
