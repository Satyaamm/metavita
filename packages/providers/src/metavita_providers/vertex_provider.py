"""Google Vertex AI adapter — Gemini chat via the generateContent REST API.

Brought by the user as a `gcp_vertex` Connection (project_id + location +
service_account_json + model). Authenticates by minting a Google OAuth token from
the service-account key (JWT-bearer grant, RS256) — no google-cloud SDK needed.
"""

from __future__ import annotations

import json
import time
from collections.abc import AsyncIterator, Sequence

import httpx

from .base import (
    AgentMessage,
    ChatMessage,
    ChatResult,
    EmbeddingResult,
    ToolDef,
    ToolTurn,
    Usage,
)

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SCOPE = "https://www.googleapis.com/auth/cloud-platform"


class VertexProvider:
    name = "gcp_vertex"

    def __init__(
        self, *, project_id: str, location: str, service_account_json: str | dict
    ) -> None:
        self._project = project_id
        self._location = location or "us-central1"
        if isinstance(service_account_json, str):
            self._sa = json.loads(service_account_json) if service_account_json else {}
        else:
            self._sa = service_account_json or {}

    async def _access_token(self) -> str:
        import jwt  # lazy: PyJWT (+cryptography) only needed for Vertex

        now = int(time.time())
        assertion = jwt.encode(
            {
                "iss": self._sa.get("client_email"),
                "scope": _SCOPE,
                "aud": _TOKEN_URL,
                "iat": now,
                "exp": now + 3600,
            },
            self._sa["private_key"],
            algorithm="RS256",
        )
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                _TOKEN_URL,
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                    "assertion": assertion,
                },
            )
            resp.raise_for_status()
            return resp.json()["access_token"]

    def _endpoint(self, model: str) -> str:
        return (
            f"https://{self._location}-aiplatform.googleapis.com/v1/projects/"
            f"{self._project}/locations/{self._location}/publishers/google/models/"
            f"{model}:generateContent"
        )

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> ChatResult:
        contents = [
            {"role": "model" if m.role == "assistant" else "user", "parts": [{"text": m.content}]}
            for m in messages
        ]
        body: dict = {"contents": contents, "generationConfig": {"maxOutputTokens": max_tokens}}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        token = await self._access_token()
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                self._endpoint(model),
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
        candidates = data.get("candidates", [])
        parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
        text = "".join(p.get("text", "") for p in parts)
        usage = data.get("usageMetadata", {}) or {}
        return ChatResult(
            text=text,
            model=model,
            usage=Usage(
                int(usage.get("promptTokenCount", 0)),
                int(usage.get("candidatesTokenCount", 0)),
            ),
            stop_reason=candidates[0].get("finishReason") if candidates else None,
        )

    async def chat_stream(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> AsyncIterator[str]:
        res = await self.chat(messages, model=model, max_tokens=max_tokens, system=system)
        if res.text:
            yield res.text

    async def chat_tools(
        self,
        messages: Sequence[AgentMessage],
        *,
        model: str,
        tools: Sequence[ToolDef],
        system: str | None = None,
        max_tokens: int = 1024,
    ) -> ToolTurn:
        flat = [ChatMessage(m.role, m.text or "") for m in messages if m.text]
        res = await self.chat(flat, model=model, max_tokens=max_tokens, system=system)
        return ToolTurn(text=res.text, tool_calls=[], stop_reason=res.stop_reason, usage=res.usage)

    async def embed(self, texts: Sequence[str], *, model: str) -> EmbeddingResult:
        raise NotImplementedError("Vertex embeddings adapter not implemented yet")
