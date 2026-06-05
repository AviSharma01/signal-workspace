"""
Deterministic anomaly trigger (§2 of AGENT_SPEC.md).

scan_watchlist() scans the combined watchlist (SEED_COMPANIES + DEMO_TICKERS)
and returns tickers whose latest bar trips the z-score or volume-ratio threshold.
No LLM involved — this is pure arithmetic over price_points.
"""

from __future__ import annotations

import logging
import math
from typing import Any

from db.database import get_connection, SEED_COMPANIES
from seed_demo import DEMO_TICKERS

logger = logging.getLogger(__name__)

# Tuneable thresholds — mirror seed_demo.py's values exactly (§2 of AGENT_SPEC.md).
N_WINDOW      = 30    # trading days of history to compute baseline
Z_THRESHOLD   = 2.0   # |z-score| of latest daily return
VOL_THRESHOLD = 2.5   # latest volume / mean(volume over window)

# (ticker, trigger_dict) pair returned for each flagged ticker.
FlaggedTicker = tuple[str, dict[str, Any]]


def scan_watchlist() -> list[FlaggedTicker]:
    """
    Scan the combined watchlist for anomalous price moves.

    Returns a list of (ticker, trigger) pairs for tickers that trip
    |z-score| >= Z_THRESHOLD or volume_ratio >= VOL_THRESHOLD.
    Tickers with fewer than N_WINDOW price bars are silently skipped.
    """
    real_tickers = [c[0] for c in SEED_COMPANIES]
    # Combine real + demo; deduplicate while preserving order.
    combined: list[str] = list(dict.fromkeys(real_tickers + list(DEMO_TICKERS)))

    flagged: list[FlaggedTicker] = []

    with get_connection() as conn:
        for ticker in combined:
            rows = conn.execute(
                "SELECT close, volume FROM price_points "
                "WHERE company_id = ? ORDER BY timestamp DESC LIMIT ?",
                (ticker, N_WINDOW),
            ).fetchall()

            if len(rows) < N_WINDOW:
                logger.debug(
                    "scan_watchlist: skipping %s — %d bars available (need %d)",
                    ticker, len(rows), N_WINDOW,
                )
                continue

            # DB returned DESC; reverse to chronological order for pct-change.
            rows = list(reversed(rows))
            closes  = [r["close"]  for r in rows]
            volumes = [r["volume"] for r in rows]

            # Population std — same math as seed_demo.trigger_check.
            returns  = [closes[i] / closes[i - 1] - 1 for i in range(1, len(closes))]
            mean_r   = sum(returns) / len(returns)
            variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
            std_r    = math.sqrt(variance) if variance > 0 else 0.0
            z        = (returns[-1] - mean_r) / std_r if std_r else 0.0

            mean_vol  = sum(volumes) / len(volumes)
            vol_ratio = volumes[-1] / mean_vol if mean_vol else 0.0

            if abs(z) >= Z_THRESHOLD or vol_ratio >= VOL_THRESHOLD:
                flagged.append((ticker, {
                    "z_score":           round(z, 2),
                    "volume_ratio":      round(vol_ratio, 2),
                    "direction":         "up" if returns[-1] > 0 else "down",
                    "latest_return_pct": round(returns[-1] * 100, 2),
                }))

    return flagged
