"""AWS Bedrock adapter — chat via the InvokeModel REST API, SigV4-signed.

Brought by the user as an `aws_bedrock` Connection (region + access keys + model).
Targets the Anthropic-Claude-on-Bedrock message family (the common case and our
default model id); other families are sent the same message body best-effort.
No boto3 dependency — requests are signed with the stdlib SigV4 helper.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Sequence

import httpx

from . import _awssig
from .base import (
    AgentMessage,
    ChatMessage,
    ChatResult,
    EmbeddingResult,
    ToolDef,
    ToolTurn,
    Usage,
)

_SERVICE = "bedrock"
_ANTHROPIC_VERSION = "bedrock-2023-05-31"


class BedrockProvider:
    name = "aws_bedrock"

    def __init__(
        self,
        *,
        region: str,
        access_key_id: str,
        secret_access_key: str,
        session_token: str | None = None,
    ) -> None:
        self._region = region or "us-east-1"
        self._access_key = access_key_id or ""
        self._secret_key = secret_access_key or ""
        self._session_token = session_token
        self._host = f"bedrock-runtime.{self._region}.amazonaws.com"

    def _body(self, messages: Sequence[ChatMessage], system: str | None, max_tokens: int) -> dict:
        body: dict = {
            "anthropic_version": _ANTHROPIC_VERSION,
            "max_tokens": max_tokens,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if system:
            body["system"] = system
        return body

    async def chat(
        self,
        messages: Sequence[ChatMessage],
        *,
        model: str,
        max_tokens: int = 4096,
        system: str | None = None,
    ) -> ChatResult:
        path = f"/model/{model}/invoke"
        payload = json.dumps(self._body(messages, system, max_tokens)).encode("utf-8")
        headers = _awssig.sigv4_headers(
            method="POST",
            host=self._host,
            path=path,
            region=self._region,
            service=_SERVICE,
            payload=payload,
            access_key=self._access_key,
            secret_key=self._secret_key,
            session_token=self._session_token,
        )
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"https://{self._host}{path}", headers=headers, content=payload
            )
            resp.raise_for_status()
            data = resp.json()
        parts = data.get("content", [])
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        usage = data.get("usage", {}) or {}
        return ChatResult(
            text=text,
            model=model,
            usage=Usage(int(usage.get("input_tokens", 0)), int(usage.get("output_tokens", 0))),
            stop_reason=data.get("stop_reason"),
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
        raise NotImplementedError("Bedrock embeddings adapter not implemented yet")
