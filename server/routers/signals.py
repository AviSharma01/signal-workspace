from fastapi import APIRouter, HTTPException

from db.database import get_connection

router = APIRouter(prefix="/api")


@router.get("/signals/{company_id}")
def get_signals(company_id: str) -> dict:
    cid = company_id.upper()

    with get_connection() as conn:
        if not conn.execute("SELECT id FROM companies WHERE id = ?", (cid,)).fetchone():
            raise HTTPException(status_code=404, detail="Company not found")

        news_rows = conn.execute(
            """
            SELECT id, company_id, headline, summary, source, url, published_at
            FROM news_items
            WHERE company_id = ?
            ORDER BY published_at DESC
            LIMIT 10
            """,
            (cid,),
        ).fetchall()

        disc_rows = conn.execute(
            """
            SELECT id, company_id, title, summary, source, url, published_at
            FROM discussion_items
            WHERE company_id = ?
            ORDER BY published_at DESC
            LIMIT 10
            """,
            (cid,),
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

    return {"news": news, "discussion": discussion}
