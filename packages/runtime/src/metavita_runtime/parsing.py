"""Extract plain text from uploaded documents by content type."""

from __future__ import annotations

import io

from bs4 import BeautifulSoup


def parse(content: bytes, *, content_type: str | None, filename: str | None) -> str:
    kind = _detect(content_type, filename)
    if kind == "pdf":
        return _parse_pdf(content)
    if kind == "docx":
        return _parse_docx(content)
    if kind == "html":
        return _parse_html(content)
    # markdown / plain text / unknown → best-effort decode.
    return content.decode("utf-8", errors="replace")


def _detect(content_type: str | None, filename: str | None) -> str:
    ct = (content_type or "").lower()
    name = (filename or "").lower()
    if "pdf" in ct or name.endswith(".pdf"):
        return "pdf"
    if "wordprocessingml" in ct or name.endswith(".docx"):
        return "docx"
    if "html" in ct or name.endswith((".html", ".htm")):
        return "html"
    return "text"


def _parse_pdf(content: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(content))
    return "\n\n".join((page.extract_text() or "") for page in reader.pages)


def _parse_docx(content: bytes) -> str:
    from docx import Document

    doc = Document(io.BytesIO(content))
    return "\n\n".join(p.text for p in doc.paragraphs if p.text)


def _parse_html(content: bytes) -> str:
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n")
