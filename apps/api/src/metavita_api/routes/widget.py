"""Serves the embeddable chat widget (`/widget.js`).

The widget is a self-contained vanilla-JS asset that renders a floating chat panel
posting to `/serve/{deployment}`. Served with permissive CORS + cache headers so it
can be embedded from any customer domain via a single <script> tag.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter(tags=["widget"])

_WIDGET_PATH = Path(__file__).resolve().parent.parent / "static" / "widget.js"


@router.get("/widget.js")
async def widget_js() -> Response:
    source = _WIDGET_PATH.read_text(encoding="utf-8")
    return Response(
        content=source,
        media_type="application/javascript",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600",
        },
    )
