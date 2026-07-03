"""Analytics time-series tests."""

from __future__ import annotations

from datetime import date

from metavita_api.services.analytics import build_daily_series


def test_fills_gaps_and_orders() -> None:
    today = date(2026, 6, 25)
    counts = {"2026-06-25": 3, "2026-06-23": 1}
    series = build_daily_series(counts, days=3, today=today)
    assert series == [
        {"date": "2026-06-23", "runs": 1},
        {"date": "2026-06-24", "runs": 0},
        {"date": "2026-06-25", "runs": 3},
    ]


def test_empty_counts() -> None:
    series = build_daily_series({}, days=2, today=date(2026, 1, 2))
    assert series == [
        {"date": "2026-01-01", "runs": 0},
        {"date": "2026-01-02", "runs": 0},
    ]
