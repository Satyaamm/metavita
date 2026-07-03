"""WebConnector tests — crawl bounding + same-domain link following (mocked HTTP)."""

from __future__ import annotations

import httpx
import pytest
from metavita_api.connectors.web import WebConnector

PAGES = {
    "https://site.test/": (
        "<html><body><a href='/about'>about</a> "
        "<a href='https://other.test/x'>off</a> hello world</body></html>"
    ),
    "https://site.test/about": "<html><body>about page content</body></html>",
    "https://other.test/x": "<html><body>should not be crawled</body></html>",
}


def _handler(request: httpx.Request) -> httpx.Response:
    body = PAGES.get(str(request.url))
    if body is None:
        return httpx.Response(404)
    return httpx.Response(200, html=body)


async def _collect(config: dict) -> list[str]:
    connector = WebConnector(transport=httpx.MockTransport(_handler))
    return [doc.filename async for doc in connector.fetch(config)]


@pytest.mark.asyncio
async def test_single_page_crawl_is_bounded():
    urls = await _collect({"url": "https://site.test/", "max_pages": 1})
    assert urls == ["https://site.test/"]


@pytest.mark.asyncio
async def test_follows_same_domain_links_up_to_max_pages():
    urls = await _collect({"url": "https://site.test/", "max_pages": 5, "same_domain": True})
    assert "https://site.test/" in urls
    assert "https://site.test/about" in urls
    # off-domain link must never be crawled when same_domain is on
    assert "https://other.test/x" not in urls


@pytest.mark.asyncio
async def test_missing_url_raises():
    connector = WebConnector(transport=httpx.MockTransport(_handler))
    with pytest.raises(ValueError, match="url"):
        async for _ in connector.fetch({}):
            pass
