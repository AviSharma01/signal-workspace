"""
seed_demo.py - Demo/eval fixtures for the Signal Investigation Agent.

Writes controlled, deterministic market scenarios into the existing SQLite DB
so the anomaly trigger fires on known events and the agent has ground-truth
answers to investigate. This single file is BOTH the demo dataset and the eval
fixture - the eval just asserts the agent reaches each ticker's known driver.

SCENARIOS (all events land on the final bar, END_DATE):
    NMBS              -> news        (clear causal headline same session)
    ORCH/HLIX/VRTA    -> sector      (peers all drop together, no news)
    DRFT              -> unexplained (trips trigger, but nothing explains it)

SAFETY: this script ONLY touches the invented tickers in DEMO_TICKERS. It never
reads, modifies, or deletes the real watchlist (AAPL/MSFT/GOOGL/AMZN/NVDA) or
any other rows. It is idempotent - re-running clears and rewrites only the demo
tickers, so your real data is always left intact.

Run from the server/ directory (same place you run uvicorn):
    python seed_demo.py
"""

from __future__ import annotations

import os
import sys
import math
import random
from datetime import datetime, timedelta, timezone

# Make `from db.database import ...` resolve when run as `python seed_demo.py`
# from inside server/ (same import pattern the routers and jobs use).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from db.database import get_connection  # noqa: E402


# ---------------------------------------------------------------------------
# Config - tune here. Z/VOL thresholds mirror the agent's anomaly trigger.
# ---------------------------------------------------------------------------
RANDOM_SEED = 42           # fixed -> byte-identical data every run
N_DAYS = 45                # trading (week)days of history per ticker
N_WINDOW = 30              # trigger baseline window (must be <= N_DAYS)
Z_THRESHOLD = 2.0          # |z-score| of the latest daily return
VOL_THRESHOLD = 2.5        # latest volume / mean(window volume)

END_DATE = datetime(2026, 5, 15, tzinfo=timezone.utc)  # last bar = event day
CLOSE_HOUR_UTC = 20        # ~16:00 ET close
BASELINE_MEAN = 0.0        # mean daily return on calm days
BASELINE_STD = 0.008       # 0.8% daily vol on calm days (keeps baseline quiet)
INTRADAY_SPREAD = 0.004    # high/low bracket around open/close
VOL_NOISE = 0.10           # +/-10% volume jitter on calm days

DEMO_TICKERS = ["NMBS", "ORCH", "HLIX", "VRTA", "DRFT"]

# id, name, sector, start_price, base_volume
COMPANIES = [
    ("NMBS", "Nimbus Software",    "Software",  180.0, 1_200_000),
    ("ORCH", "Orchid Biosciences", "Biotech",    60.0, 1_500_000),
    ("HLIX", "Helix Therapeutics", "Biotech",    95.0,   900_000),
    ("VRTA", "Vertica Biotech",    "Biotech",    42.0, 1_100_000),
    ("DRFT", "Drift Dynamics",     "Logistics",  75.0,   800_000),
]

# ticker -> (event_return, volume_multiplier) applied on END_DATE.
# Note: the price move alone trips the z-score trigger; the volume multiplier
# is for realism and so get_price_movement can report elevated volume.
EVENTS = {
    "NMBS": (-0.065, 3.3),   # news-driven   (sector "Software", no peers here)
    "ORCH": (-0.045, 2.9),   # sector        }
    "HLIX": (-0.048, 3.0),   # sector        } same-day co-movement, no news
    "VRTA": (-0.042, 2.9),   # sector        }
    "DRFT": (-0.050, 2.9),   # unexplained   (sector "Logistics", no peers, no news)
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def trading_days(end: datetime, n: int) -> list[datetime]:
    """The n most recent weekdays up to and including `end` (or the nearest
    prior weekday), chronological order, timestamped at market close."""
    out: list[datetime] = []
    d = end
    while len(out) < n:
        if d.weekday() < 5:  # Mon-Fri
            out.append(d.replace(hour=CLOSE_HOUR_UTC, minute=0, second=0, microsecond=0))
        d -= timedelta(days=1)
    return list(reversed(out))


def to_ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def generate_ohlcv(rng: random.Random, start_price: float, base_volume: int,
                   days: list[datetime], event: tuple[float, float] | None) -> list[dict]:
    """Daily OHLCV bars. Calm baseline + one engineered move on the last bar
    if `event` is set."""
    bars: list[dict] = []
    prev_close = start_price
    last_idx = len(days) - 1
    for i, day in enumerate(days):
        is_event = event is not None and i == last_idx
        ret = event[0] if is_event else rng.gauss(BASELINE_MEAN, BASELINE_STD)
        close = prev_close * (1 + ret)
        open_ = prev_close * (1 + rng.gauss(0, BASELINE_STD / 2))
        high = max(open_, close) * (1 + abs(rng.gauss(0, INTRADAY_SPREAD)))
        low = min(open_, close) * (1 - abs(rng.gauss(0, INTRADAY_SPREAD)))
        volume = (int(base_volume * event[1]) if is_event
                  else int(base_volume * (1 + rng.uniform(-VOL_NOISE, VOL_NOISE))))
        bars.append({
            "timestamp": to_ms(day),
            "open": round(open_, 2), "high": round(high, 2),
            "low": round(low, 2), "close": round(close, 2),
            "volume": volume,
        })
        prev_close = close
    return bars


def news_rows(days: list[datetime]) -> list[dict]:
    """Causal headline for NMBS on the event day, plus one stale distractor.

    The distractor (a non-causal ORCH item dated ~9 sessions before the move)
    tests whether the agent reasons about TIMING rather than blaming the
    nearest available headline. Delete the second dict if it muddies early
    testing - A/B/C still hold without it.
    """
    event_day = days[-1]
    distractor_day = days[-10]  # ~9 weekdays before the event
    return [
        {
            "id": "seed-news-nmbs-001",
            "company_id": "NMBS",
            "headline": "Nimbus Software cuts full-year revenue guidance amid enterprise slowdown",
            "summary": ("Nimbus lowered its full-year revenue outlook, citing slower enterprise "
                        "renewals and longer sales cycles, and withdrew prior margin targets."),
            "source": "DemoWire",
            "url": "https://example.com/nmbs-guidance-cut",
            "published_at": to_ms(event_day.replace(hour=13, minute=30)),
        },
        {  # OPTIONAL distractor - see docstring above.
            "id": "seed-news-orch-001",
            "company_id": "ORCH",
            "headline": "Orchid Biosciences to present at upcoming industry conference",
            "summary": ("Orchid confirmed its scheduled participation in an industry conference. "
                        "No financial guidance or material update was provided."),
            "source": "DemoWire",
            "url": "https://example.com/orch-conference",
            "published_at": to_ms(distractor_day.replace(hour=14, minute=0)),
        },
    ]


def trigger_check(closes: list[float], volumes: list[int]) -> tuple[float, float]:
    """Recompute the agent's trigger over the final window so we verify, at
    seed time, that each event actually fires."""
    wc = closes[-N_WINDOW:]
    wv = volumes[-N_WINDOW:]
    returns = [wc[i] / wc[i - 1] - 1 for i in range(1, len(wc))]
    mean_r = sum(returns) / len(returns)
    std = math.sqrt(sum((r - mean_r) ** 2 for r in returns) / len(returns))
    z = (returns[-1] - mean_r) / std if std else 0.0
    vol_ratio = wv[-1] / (sum(wv) / len(wv))
    return z, vol_ratio


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------
def seed() -> None:
    rng = random.Random(RANDOM_SEED)
    days = trading_days(END_DATE, N_DAYS)
    report: dict[str, tuple[float, float]] = {}

    with get_connection() as conn:
        cur = conn.cursor()
        ph = ",".join("?" for _ in DEMO_TICKERS)

        # SAFETY: clear ONLY demo tickers. Real watchlist rows are never touched.
        cur.execute(f"DELETE FROM price_points     WHERE company_id IN ({ph})", DEMO_TICKERS)
        cur.execute(f"DELETE FROM news_items        WHERE company_id IN ({ph})", DEMO_TICKERS)
        cur.execute(f"DELETE FROM discussion_items  WHERE company_id IN ({ph})", DEMO_TICKERS)
        cur.execute(f"DELETE FROM companies         WHERE id         IN ({ph})", DEMO_TICKERS)

        cur.executemany(
            "INSERT INTO companies (id, name, sector) VALUES (?, ?, ?)",
            [(c[0], c[1], c[2]) for c in COMPANIES],
        )

        for cid, _name, _sector, start, base_vol in COMPANIES:
            bars = generate_ohlcv(rng, start, base_vol, days, EVENTS.get(cid))
            cur.executemany(
                "INSERT INTO price_points "
                "(company_id, timestamp, open, high, low, close, volume) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(cid, b["timestamp"], b["open"], b["high"], b["low"], b["close"], b["volume"])
                 for b in bars],
            )
            report[cid] = trigger_check([b["close"] for b in bars],
                                        [b["volume"] for b in bars])

        cur.executemany(
            "INSERT INTO news_items "
            "(id, company_id, headline, summary, source, url, published_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            [(n["id"], n["company_id"], n["headline"], n["summary"],
              n["source"], n["url"], n["published_at"]) for n in news_rows(days)],
        )

    # Verify-and-report: catch a non-firing event NOW, not during the demo.
    print(f"\nSeeded {len(COMPANIES)} demo tickers x {N_DAYS} daily bars.")
    print(f"Window {days[0].date()} -> {days[-1].date()}  (event day = {days[-1].date()})\n")
    print(f"{'Ticker':<8}{'z-score':>10}{'vol_ratio':>12}   fires?")
    print("-" * 44)
    all_fire = True
    for cid, *_ in COMPANIES:
        z, vr = report[cid]
        fires = abs(z) >= Z_THRESHOLD or vr >= VOL_THRESHOLD
        all_fire &= fires
        print(f"{cid:<8}{z:>10.2f}{vr:>12.2f}   {'YES' if fires else 'NO'}")
    print("-" * 44)
    if not all_fire:
        raise SystemExit("\nERROR: an event ticker does not trip the trigger. "
                         "Adjust EVENTS or thresholds and re-run.")
    print("\nAll events trip the trigger. Ground truth:")
    print("  NMBS -> news   |   ORCH/HLIX/VRTA -> sector   |   DRFT -> unexplained\n")


if __name__ == "__main__":
    seed()