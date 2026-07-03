"""Thin, typed async client over the MetaVita REST API.

Mirrors the TypeScript SDK. Two auth modes:
  - ``api_key`` → a deployment key for the public ``/serve/{id}`` surface.
  - ``token``   → a workspace JWT for authenticated builder endpoints.

Example::

    async with MetaVita("https://api.metavita.dev", api_key="mv_...") as mv:
        res = await mv.serve(deployment_id, question="What changed in v2?")
        print(res.answer, res.citations)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import TracebackType
from typing import Any

import httpx


class MetaVitaError(RuntimeError):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"[{status}] {message}")
        self.status = status
        self.message = message


@dataclass(slots=True)
class Citation:
    marker: int
    document_id: str | None
    chunk_index: int | None
    snippet: str


@dataclass(slots=True)
class AnswerResponse:
    answer: str
    citations: list[Citation] = field(default_factory=list)
    run_id: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AnswerResponse:
        return cls(
            answer=data.get("answer", ""),
            citations=[Citation(**c) for c in data.get("citations", [])],
            run_id=data.get("run_id"),
        )


class MetaVita:
    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        token: str | None = None,
        workspace_id: str | None = None,
        client: httpx.AsyncClient | None = None,
        timeout: float = 60.0,
    ) -> None:
        if not base_url:
            raise ValueError("MetaVita: base_url is required")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._token = token
        self._workspace_id = workspace_id
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._owns_client = client is None

    async def __aenter__(self) -> MetaVita:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _headers(self, *, use_key: bool) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if use_key and self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        elif self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        if self._workspace_id:
            headers["X-Workspace-Id"] = self._workspace_id
        return headers

    async def _request(
        self, method: str, path: str, *, json: dict | None = None, use_key: bool = False
    ) -> Any:
        resp = await self._client.request(
            method, f"{self._base_url}{path}", json=json, headers=self._headers(use_key=use_key)
        )
        if resp.status_code >= 400:
            raise MetaVitaError(resp.status_code, resp.text)
        if resp.status_code == 204:
            return None
        return resp.json()

    # --- public serving ----------------------------------------------------
    async def serve(self, deployment_id: str, *, question: str, k: int = 5) -> AnswerResponse:
        data = await self._request(
            "POST", f"/serve/{deployment_id}", json={"question": question, "k": k}, use_key=True
        )
        return AnswerResponse.from_dict(data)

    # --- authenticated builder API -----------------------------------------
    async def query(self, *, question: str, k: int = 5) -> AnswerResponse:
        data = await self._request("POST", "/query", json={"question": question, "k": k})
        return AnswerResponse.from_dict(data)

    async def run_pipeline(self, pipeline_id: str, *, question: str, k: int = 5) -> AnswerResponse:
        data = await self._request(
            "POST", f"/pipelines/{pipeline_id}/run", json={"question": question, "k": k}
        )
        return AnswerResponse.from_dict(data)

    async def run_agent(self, agent_id: str, *, message: str, k: int = 5) -> dict[str, Any]:
        return await self._request(
            "POST", f"/agents/{agent_id}/run", json={"message": message, "k": k}
        )

    async def list_pipelines(self) -> list[dict[str, Any]]:
        return (await self._request("GET", "/pipelines"))["items"]

    async def list_agents(self) -> list[dict[str, Any]]:
        return (await self._request("GET", "/agents"))["items"]

    async def crawl(
        self, *, url: str, max_pages: int = 1, same_domain: bool = True, name: str | None = None
    ) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/knowledge/crawl",
            json={"url": url, "max_pages": max_pages, "same_domain": same_domain, "name": name},
        )
