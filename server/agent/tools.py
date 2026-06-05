"""
Read-only tool functions for the signal investigation agent.

All four tools SELECT only — they never write, send, or call external services.
Window anchoring: all time-windowed queries anchor to the most recent
price_points.timestamp for the ticker, not to datetime.now(), so the agent
reasons against the DB's timeline (historical seeded data).
"""

from __future__ import annotations

import math
from typing import Any

from db.database import get_connection

_MS_PER_DAY = 86_400_000


def _anchor_ms(ticker: str) -> int | None:
    """Return the most recent price_points.timestamp for ticker, or None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT MAX(timestamp) AS ts FROM price_points WHERE company_id = ?",
            (ticker,),
        ).fetchone()
    return row["ts"] if row and row["ts"] is not None else None


# ---------------------------------------------------------------------------
# Tool 1
# ---------------------------------------------------------------------------

def get_price_movement(ticker: str, window_days: int = 30) -> dict[str, Any]:
    """
    Quantify the price move for *ticker* over the last *window_days* calendar
    days, anchored to the most recent bar in the DB.

    Returns z-score, volume ratio, direction, and the full series so the agent
    can ground its reasoning in the actual numbers.
    """
    anchor = _anchor_ms(ticker)
    if anchor is None:
        return {
            "ticker": ticker, "latest_close": None, "latest_return_pct": None,
            "z_score": None, "volume_ratio": None, "direction": None, "series": [],
        }

    window_start = anchor - window_days * _MS_PER_DAY

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT timestamp, open, high, low, close, volume "
            "FROM price_points "
            "WHERE company_id = ? AND timestamp >= ? "
            "ORDER BY timestamp ASC",
            (ticker, window_start),
        ).fetchall()

    if not rows:
        return {
            "ticker": ticker, "latest_close": None, "latest_return_pct": None,
            "z_score": None, "volume_ratio": None, "direction": None, "series": [],
        }

    series = [
        {"timestamp": r["timestamp"], "close": r["close"], "volume": r["volume"]}
        for r in rows
    ]

    closes = [r["close"] for r in rows]
    volumes = [r["volume"] for r in rows]

    if len(closes) < 2:
        return {
            "ticker": ticker,
            "latest_close": closes[-1],
            "latest_return_pct": None,
            "z_score": None,
            "volume_ratio": None,
            "direction": None,
            "series": series,
        }

    returns = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
    latest_return = returns[-1]
    mean_r = sum(returns) / len(returns)
    variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
    std_r = math.sqrt(variance)
    z_score = (latest_return - mean_r) / std_r if std_r != 0 else 0.0

    mean_vol = sum(volumes) / len(volumes)
    volume_ratio = volumes[-1] / mean_vol if mean_vol != 0 else 0.0

    return {
        "ticker": ticker,
        "latest_close": round(closes[-1], 4),
        "latest_return_pct": round(latest_return * 100, 4),
        "z_score": round(z_score, 4),
        "volume_ratio": round(volume_ratio, 4),
        "direction": "up" if latest_return > 0 else "down",
        "series": series,
    }


# ---------------------------------------------------------------------------
# Tool 2
# ---------------------------------------------------------------------------

def get_news(ticker: str, window_days: int = 7) -> list[dict[str, Any]]:
    """
    Return news items for *ticker* published within *window_days* calendar days
    before the most recent price bar, newest first.
    """
    anchor = _anchor_ms(ticker)
    if anchor is None:
        return []

    window_start = anchor - window_days * _MS_PER_DAY

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT headline, summary, source, published_at "
            "FROM news_items "
            "WHERE company_id = ? AND published_at >= ? "
            "ORDER BY published_at DESC",
            (ticker, window_start),
        ).fetchall()

    return [
        {
            "headline": r["headline"],
            "summary": r["summary"],
            "source": r["source"],
            "published_at": r["published_at"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Tool 3
# ---------------------------------------------------------------------------

def get_discussion(ticker: str, window_days: int = 7) -> list[dict[str, Any]]:
    """
    Return social/forum discussion for *ticker* within *window_days* calendar
    days before the most recent price bar, newest first.

    DB quirk: discussion_items.title holds the message body; summary is always
    empty. This function normalizes that away — callers receive body, not title,
    and the empty summary field is dropped.
    """
    anchor = _anchor_ms(ticker)
    if anchor is None:
        return []

    window_start = anchor - window_days * _MS_PER_DAY

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT title, source, published_at "
            "FROM discussion_items "
            "WHERE company_id = ? AND published_at >= ? "
            "ORDER BY published_at DESC",
            (ticker, window_start),
        ).fetchall()

    return [
        {
            "body": r["title"],
            "source": r["source"],
            "published_at": r["published_at"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Tool 4
# ---------------------------------------------------------------------------

def get_related_companies(ticker: str) -> list[dict[str, Any]]:
    """
    Return all companies in the same sector as *ticker*, excluding *ticker*
    itself. Used by the agent to distinguish idiosyncratic moves from
    sector-wide ones.
    """
    with get_connection() as conn:
        sector_row = conn.execute(
            "SELECT sector FROM companies WHERE id = ?", (ticker,)
        ).fetchone()

        if sector_row is None:
            return []

        sector = sector_row["sector"]

        rows = conn.execute(
            "SELECT id, name, sector FROM companies WHERE sector = ? AND id != ?",
            (sector, ticker),
        ).fetchall()

    return [
        {"ticker": r["id"], "name": r["name"], "sector": r["sector"]}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Verification — run from server/ with: python -m agent.tools
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    def show(label: str, value: Any) -> None:
        print(f"\n{'=' * 60}")
        print(f"  {label}")
        print('=' * 60)
        if isinstance(value, list):
            if not value:
                print("  (empty list)")
            else:
                for item in value:
                    print(json.dumps(item, indent=4))
        elif isinstance(value, dict):
            # Omit series for brevity; print it separately
            series = value.pop("series", None)
            print(json.dumps(value, indent=4))
            if series is not None:
                print(f"  series: {len(series)} bars")
                if series:
                    print(f"  latest bar: {json.dumps(series[-1], indent=4)}")
        else:
            print(value)

    # 1. NMBS price movement — expect ~-6.5% return, ~3x volume
    pm = get_price_movement("NMBS")
    show("get_price_movement('NMBS') — expect ~-6.5% return, ~3x volume", pm)

    # 2. NMBS news — expect guidance-cut headline
    show("get_news('NMBS') — expect guidance-cut headline", get_news("NMBS"))

    # 3. ORCH news, default 7-day window — expect empty (distractor is ~9 sessions old)
    show("get_news('ORCH', window_days=7) — expect empty (distractor too old)", get_news("ORCH", window_days=7))

    # 4. ORCH news, 14-day window — expect stale conference distractor
    show("get_news('ORCH', window_days=14) — expect stale conference distractor", get_news("ORCH", window_days=14))

    # 5. NMBS discussion — expect empty (none seeded)
    show("get_discussion('NMBS') — expect empty list", get_discussion("NMBS"))

    # 6. ORCH related companies — expect HLIX and VRTA (Biotech); not ORCH
    show("get_related_companies('ORCH') — expect HLIX + VRTA, no ORCH", get_related_companies("ORCH"))

    # 7. DRFT related companies — expect empty (sole Logistics ticker)
    show("get_related_companies('DRFT') — expect empty list", get_related_companies("DRFT"))
