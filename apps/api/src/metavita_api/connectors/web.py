"""Web-crawl connector — fetches a start URL and (optionally) same-domain links.

Bounded by `max_pages` and `same_domain` so a crawl can't run away. Each page is
yielded as an HTML `FetchedDoc`; the runtime's HTML parser extracts text downstream.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from .base import Connector, FetchedDoc

_DEFAULT_TIMEOUT = 15.0
_MAX_PAGES_CAP = 50


class WebConnector(Connector):
    name = "web"

    def __init__(self, *, transport: httpx.AsyncBaseTransport | None = None) -> None:
        # Injectable transport keeps the crawler unit-testable without real network.
        self._transport = transport

    async def fetch(self, config: dict) -> AsyncIterator[FetchedDoc]:
        start = (config.get("url") or "").strip()
        if not start:
            raise ValueError("web connector requires a 'url'")
        max_pages = min(int(config.get("max_pages", 1)), _MAX_PAGES_CAP)
        same_domain = bool(config.get("same_domain", True))
        start_host = urlparse(start).netloc

        seen: set[str] = set()
        queue: list[str] = [start]
        headers = {"User-Agent": "MetaVitaCrawler/0.1 (+https://metavita.dev)"}

        async with httpx.AsyncClient(
            timeout=_DEFAULT_TIMEOUT,
            follow_redirects=True,
            headers=headers,
            transport=self._transport,
        ) as client:
            while queue and len(seen) < max_pages:
                url, _ = urldefrag(queue.pop(0))
                if url in seen:
                    continue
                seen.add(url)
                try:
                    resp = await client.get(url)
                    resp.raise_for_status()
                except httpx.HTTPError:
                    continue
                content_type = resp.headers.get("content-type", "text/html")
                if "html" not in content_type and "text" not in content_type:
                    continue
                body = resp.content
                yield FetchedDoc(
                    filename=url,
                    content=body,
                    content_type="text/html",
                    meta={"url": url, "source": "web"},
                )
                if len(seen) < max_pages:
                    queue.extend(
                        self._links(body, base=url, host=start_host, same_domain=same_domain)
                    )

    @staticmethod
    def _links(body: bytes, *, base: str, host: str, same_domain: bool) -> list[str]:
        soup = BeautifulSoup(body, "html.parser")
        out: list[str] = []
        for a in soup.find_all("a", href=True):
            link = urljoin(base, a["href"])
            if not link.startswith(("http://", "https://")):
                continue
            if same_domain and urlparse(link).netloc != host:
                continue
            out.append(link)
        return out
