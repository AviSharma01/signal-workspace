import time
from typing import Literal

from fastapi import APIRouter, HTTPException

from capabilities import result_state
from db.database import get_connection
from routers.capabilities import capability_json

router = APIRouter(prefix="/api")


@router.get("/signals/{company_id}")
def get_signals(company_id: str, population: Literal["real", "demo"] = "real") -> dict:
    cid = company_id.upper()

    with get_connection() as conn:
        if not conn.execute(
            "SELECT id FROM companies WHERE id = ? AND population = ?", (cid, population)
        ).fetchone():
            raise HTTPException(status_code=404, detail="Company not found")

        news_rows = conn.execute(
            """
            SELECT id, company_id, headline, summary, source, url, published_at
            FROM news_items
            WHERE company_id = ? AND population = ?
            ORDER BY published_at DESC
            LIMIT 10
            """,
            (cid, population),
        ).fetchall()

        disc_rows = conn.execute(
            """
            SELECT id, company_id, title, summary, source, url, published_at
            FROM discussion_items
            WHERE company_id = ? AND population = ?
            ORDER BY published_at DESC
            LIMIT 10
            """,
            (cid, population),
        ).fetchall()

    news = [
        {
            "id": r["id"],
            "companyId": r["company_id"],
            "headline": r["headline"],
            "summary": r["summary"] or "",
            "source": r["source"] or "",
            "url": r["url"] or "",
            "publishedAt": r["published_at"],
        }
        for r in news_rows
    ]

    discussion = [
        {
            "id": r["id"],
            "companyId": r["company_id"],
            "title": r["title"],
            "summary": r["summary"] or "",
            "source": r["source"] or "",
            "url": r["url"] or "",
            "publishedAt": r["published_at"],
        }
        for r in disc_rows
    ]

    evaluated_at = int(time.time() * 1000)
    return {
        "classification": "legacy_v1_context",
        "v2Capability": False,
        "detail": "These context records are not V2 Events, candidate relationships, verified relationships, anomalies, or Findings.",
        "result": capability_json(
            result_state(
                "successful" if news or discussion else "empty",
                "Legacy V1 context loaded." if news or discussion else "No legacy V1 context records exist.",
                evaluated_at=evaluated_at,
            )
        ),
        "news": news,
        "discussion": discussion,
    }
