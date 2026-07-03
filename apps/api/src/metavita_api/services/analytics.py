"""Analytics helpers — pure time-series shaping (testable)."""

from __future__ import annotations

from datetime import date, timedelta


def build_daily_series(counts: dict[str, int], *, days: int, today: date) -> list[dict]:
    """Return a gap-filled, chronologically ordered series for the last `days` days."""
    series: list[dict] = []
    for i in range(days - 1, -1, -1):
        key = (today - timedelta(days=i)).isoformat()
        series.append({"date": key, "runs": counts.get(key, 0)})
    return series
