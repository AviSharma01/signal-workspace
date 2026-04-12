from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Query

from db.database import get_connection

router = APIRouter(prefix="/api")

_RANGE_DELTAS: dict[str, timedelta] = {
    "1D": timedelta(days=1),
    "1W": timedelta(weeks=1),
    "1M": timedelta(days=30),
    "3M": timedelta(days=90),
}


@router.get("/prices/{company_id}")
def get_prices(
    company_id: str,
    range: str = Query(default="1D", pattern="^(1D|1W|1M|3M)$"),
) -> list[dict]:
    cid = company_id.upper()
    since_ms = int((datetime.now(timezone.utc) - _RANGE_DELTAS[range]).timestamp() * 1000)

    with get_connection() as conn:
        if not conn.execute("SELECT id FROM companies WHERE id = ?", (cid,)).fetchone():
            raise HTTPException(status_code=404, detail="Company not found")

        rows = conn.execute(
            """
            SELECT company_id, timestamp, open, high, low, close, volume
            FROM price_points
            WHERE company_id = ? AND timestamp >= ?
            ORDER BY timestamp ASC
            """,
            (cid, since_ms),
        ).fetchall()

    return [
        {
            "companyId": r["company_id"],
            "timestamp": r["timestamp"],
            "open": r["open"],
            "high": r["high"],
            "low": r["low"],
            "close": r["close"],
            "volume": r["volume"],
        }
        for r in rows
    ]
