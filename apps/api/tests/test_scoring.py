"""Eval scoring tests."""

from __future__ import annotations

from metavita_api.services.scoring import keyword_overlap, score_item, summarize


def test_keyword_overlap() -> None:
    assert keyword_overlap("the sky is blue", "the sky is blue") == 1.0
    assert keyword_overlap("the sky is blue", "grass is green") == 0.25  # only "is"
    assert keyword_overlap("", "anything") == 0.0


def test_score_item_grounded_with_citations() -> None:
    s = score_item(expected="sky is blue", answer="The sky is blue.", citations_count=2)
    assert s["grounded"] is True
    assert s["has_citations"] is True
    assert s["keyword_overlap"] == 1.0


def test_score_item_empty_answer() -> None:
    s = score_item(expected=None, answer="", citations_count=0)
    assert s["grounded"] is False
    assert s["has_citations"] is False
    assert s["keyword_overlap"] is None


def test_summarize_aggregates() -> None:
    results = [
        {
            "score": {"grounded": True, "has_citations": True, "keyword_overlap": 1.0},
            "latency_ms": 100,
        },
        {
            "score": {"grounded": True, "has_citations": False, "keyword_overlap": 0.5},
            "latency_ms": 200,
        },
    ]
    summary = summarize(results)
    assert summary["count"] == 2
    assert summary["grounded"] == 2
    assert summary["with_citations"] == 1
    assert summary["avg_keyword_overlap"] == 0.75
    assert summary["avg_latency_ms"] == 150
