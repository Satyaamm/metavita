"""Recursive character text splitter with overlap.

Deliberately dependency-light: splits on a descending list of separators
(paragraphs → lines → sentences → words) so chunks stay semantically coherent,
then enforces a max size with overlap for retrieval recall.
"""

from __future__ import annotations

_SEPARATORS = ["\n\n", "\n", ". ", " "]


def _split_recursive(text: str, size: int, seps: list[str]) -> list[str]:
    if len(text) <= size:
        return [text] if text.strip() else []
    if not seps:
        # No separators left — hard-split.
        return [text[i : i + size] for i in range(0, len(text), size)]

    sep, *rest = seps
    parts = text.split(sep)
    chunks: list[str] = []
    buf = ""
    for part in parts:
        candidate = part if not buf else f"{buf}{sep}{part}"
        if len(candidate) <= size:
            buf = candidate
        else:
            if buf:
                chunks.append(buf)
            if len(part) > size:
                chunks.extend(_split_recursive(part, size, rest))
                buf = ""
            else:
                buf = part
    if buf.strip():
        chunks.append(buf)
    return chunks


def chunk_text(text: str, *, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    """Split text into overlapping chunks of roughly `chunk_size` characters."""
    text = text.strip()
    if not text:
        return []
    base = _split_recursive(text, chunk_size, _SEPARATORS)
    if overlap <= 0 or len(base) <= 1:
        return base

    overlapped: list[str] = []
    for i, chunk in enumerate(base):
        if i == 0:
            overlapped.append(chunk)
        else:
            tail = base[i - 1][-overlap:]
            overlapped.append(f"{tail}{chunk}")
    return overlapped
