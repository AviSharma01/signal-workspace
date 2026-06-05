from fastapi import APIRouter, Query

from agent.findings_store import list_findings

router = APIRouter(prefix="/api")


@router.get("/findings")
def get_findings(
    ticker: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1),
) -> dict:
    clamped = min(limit, 200)
    rows = list_findings(
        limit=clamped,
        ticker=ticker.upper() if ticker else None,
    )
    return {
        "findings": [
            {
                "id":               r["id"],
                "companyId":        r["company_id"],
                "createdAt":        r["created_at"],
                "trigger":          r["trigger"],
                "primaryDriver":    r["primary_driver"],
                "hypothesis":       r["hypothesis"],
                "evidence":         r["evidence"],
                "confidence":       r["confidence"],
                "needsHumanReview": r["needs_human_review"],
                "iterations":       r["iterations"],
                "costUsd":          r["cost_usd"],
            }
            for r in rows
        ]
    }
