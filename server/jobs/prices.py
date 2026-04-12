from datetime import datetime
from zoneinfo import ZoneInfo

import yfinance as yf

from db.database import get_connection, SEED_COMPANIES

_TICKERS = [c[0] for c in SEED_COMPANIES]
_ET = ZoneInfo("America/New_York")


def _is_market_hours() -> bool:
    now = datetime.now(_ET)
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    return market_open <= now <= market_close


def fetch_prices() -> None:
    if not _is_market_hours():
        return

    rows: list[tuple] = []

    for ticker in _TICKERS:
        try:
            hist = yf.Ticker(ticker).history(period="1d", interval="5m")
            for ts, row in hist.iterrows():
                timestamp_ms = int(ts.timestamp() * 1000)
                rows.append((
                    ticker,
                    timestamp_ms,
                    float(row["Open"]),
                    float(row["High"]),
                    float(row["Low"]),
                    float(row["Close"]),
                    int(row["Volume"]),
                ))
        except Exception:
            continue

    if not rows:
        return

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO price_points
              (company_id, timestamp, open, high, low, close, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
