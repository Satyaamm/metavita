"""Connectivity probes for integrations — lightweight, read-only checks.

Each tester takes the merged connection values and pings the provider's cheapest
"are these creds valid" endpoint (list models / list collections / health). Network
or auth failures return ok=False with a readable message (so an offline box reports
"unreachable" rather than crashing).
"""

from __future__ import annotations

import httpx

from .base import TestResult

_TIMEOUT = 12.0


async def _probe(method: str, url: str, *, headers: dict | None = None) -> TestResult:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.request(method, url, headers=headers or {})
        if resp.status_code in (200, 204):
            return TestResult(True, "Connected.")
        if resp.status_code in (401, 403):
            return TestResult(False, f"Authentication failed (HTTP {resp.status_code}).")
        return TestResult(False, f"Unexpected response (HTTP {resp.status_code}).")
    except httpx.HTTPError as exc:
        return TestResult(False, f"Unreachable: {exc.__class__.__name__}")


def _need(values: dict, *keys: str) -> TestResult | None:
    missing = [k for k in keys if not values.get(k)]
    return TestResult(False, f"missing: {', '.join(missing)}") if missing else None


# --- OpenAI-compatible (OpenAI, Mistral, Groq, Together, OpenRouter, custom) -----
async def openai_compatible(values: dict) -> TestResult:
    if (e := _need(values, "api_key")):
        return e
    base = (values.get("base_url") or "https://api.openai.com/v1").rstrip("/")
    auth = {"Authorization": f"Bearer {values['api_key']}"}
    return await _probe("GET", f"{base}/models", headers=auth)


async def anthropic(values: dict) -> TestResult:
    if (e := _need(values, "api_key")):
        return e
    return await _probe(
        "GET",
        "https://api.anthropic.com/v1/models",
        headers={"x-api-key": values["api_key"], "anthropic-version": "2023-06-01"},
    )


async def azure_openai(values: dict) -> TestResult:
    if (e := _need(values, "endpoint", "api_key")):
        return e
    endpoint = values["endpoint"].rstrip("/")
    ver = values.get("api_version") or "2024-06-01"
    return await _probe(
        "GET",
        f"{endpoint}/openai/deployments?api-version={ver}",
        headers={"api-key": values["api_key"]},
    )


async def cohere(values: dict) -> TestResult:
    if (e := _need(values, "api_key")):
        return e
    return await _probe(
        "GET", "https://api.cohere.com/v1/models",
        headers={"Authorization": f"Bearer {values['api_key']}"},
    )


async def ollama(values: dict) -> TestResult:
    base = (values.get("base_url") or "http://localhost:11434").rstrip("/")
    return await _probe("GET", f"{base}/api/tags")


# --- Vector stores -----------------------------------------------------------
async def pinecone(values: dict) -> TestResult:
    if (e := _need(values, "api_key")):
        return e
    return await _probe(
        "GET", "https://api.pinecone.io/indexes", headers={"Api-Key": values["api_key"]}
    )


async def qdrant(values: dict) -> TestResult:
    if (e := _need(values, "url")):
        return e
    headers = {"api-key": values["api_key"]} if values.get("api_key") else {}
    return await _probe("GET", f"{values['url'].rstrip('/')}/collections", headers=headers)


async def weaviate(values: dict) -> TestResult:
    if (e := _need(values, "url")):
        return e
    headers = {"Authorization": f"Bearer {values['api_key']}"} if values.get("api_key") else {}
    return await _probe("GET", f"{values['url'].rstrip('/')}/v1/.well-known/ready", headers=headers)


async def chroma(values: dict) -> TestResult:
    if (e := _need(values, "url")):
        return e
    return await _probe("GET", f"{values['url'].rstrip('/')}/api/v1/heartbeat")
