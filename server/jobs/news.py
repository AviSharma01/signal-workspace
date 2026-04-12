from datetime import datetime

import yfinance as yf

from db.database import get_connection, SEED_COMPANIES

_TICKERS = [c[0] for c in SEED_COMPANIES]


def _parse_timestamp(pub_date: str) -> int:
    dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
    return int(dt.timestamp() * 1000)


def fetch_news() -> None:
    rows: list[tuple] = []

    for ticker in _TICKERS:
        try:
            articles = yf.Ticker(ticker).news
            for article in (articles or [])[:5]:
                content = article.get("content", {})
                url = (content.get("canonicalUrl") or {}).get("url", "")
                if not url:
                    continue
                rows.append((
                    article["id"],
                    ticker,
                    content.get("title") or "",
                    content.get("summary") or "",
                    (content.get("provider") or {}).get("displayName") or "",
                    url,
                    _parse_timestamp(content["pubDate"]),
                ))
        except Exception:
            continue

    if not rows:
        return

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO news_items
              (id, company_id, headline, summary, source, url, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
