"""Eval scoring — pure, testable heuristics for a single answer.

MVP metrics: grounded (non-empty answer), has_citations, and keyword overlap with
an optional expected answer. LLM-judge scoring can be added later behind the same shape.
"""

from __future__ import annotations

import re


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def keyword_overlap(expected: str, answer: str) -> float:
    expected_tokens = _tokens(expected)
    if not expected_tokens:
        return 0.0
    return round(len(expected_tokens & _tokens(answer)) / len(expected_tokens), 3)


def score_item(*, expected: str | None, answer: str, citations_count: int) -> dict:
    return {
        "grounded": bool(answer and answer.strip()),
        "has_citations": citations_count > 0,
        "keyword_overlap": keyword_overlap(expected, answer) if expected else None,
    }


def summarize(results: list[dict]) -> dict:
    n = len(results)
    if n == 0:
        return {
            "count": 0,
            "grounded": 0,
            "with_citations": 0,
            "avg_keyword_overlap": None,
            "avg_latency_ms": None,
        }
    overlaps = [
        r["score"]["keyword_overlap"]
        for r in results
        if r["score"]["keyword_overlap"] is not None
    ]
    latencies = [r["latency_ms"] for r in results if r.get("latency_ms") is not None]
    return {
        "count": n,
        "grounded": sum(1 for r in results if r["score"]["grounded"]),
        "with_citations": sum(1 for r in results if r["score"]["has_citations"]),
        "avg_keyword_overlap": round(sum(overlaps) / len(overlaps), 3) if overlaps else None,
        "avg_latency_ms": round(sum(latencies) / len(latencies)) if latencies else None,
    }
