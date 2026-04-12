import json
import os
import urllib.request
from datetime import datetime

from dotenv import load_dotenv

from db.database import get_connection, SEED_COMPANIES

load_dotenv()

_TICKERS = [c[0] for c in SEED_COMPANIES]


def _parse_timestamp(created_at: str) -> int:
    dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)


def fetch_discussion() -> None:
    token = os.getenv("STOCKTWITS_TOKEN")
    rows: list[tuple] = []

    for ticker in _TICKERS:
        try:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
            if token:
                url += f"?access_token={token}"

            req = urllib.request.Request(url, headers={"User-Agent": "signal-workspace/1.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())

            for msg in data.get("messages", [])[:5]:
                rows.append((
                    str(msg["id"]),
                    ticker,
                    msg["body"],
                    "",  # title-only — body is short enough to serve as the title
                    "Stocktwits",
                    f"https://stocktwits.com/message/{msg['id']}",
                    _parse_timestamp(msg["created_at"]),
                ))
        except Exception:
            continue

    if not rows:
        return

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO discussion_items
              (id, company_id, title, summary, source, url, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
