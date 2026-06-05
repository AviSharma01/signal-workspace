"""
Persistence helpers for the findings table.

insert_finding writes a validated Finding plus loop metadata to the DB.
list_findings reads rows back as plain dicts (snake_case keys; the router
normalizes to camelCase per existing convention).
"""

from __future__ import annotations

import json
import time
import uuid

from agent.finding import Finding
from db.database import get_connection


def insert_finding(
    finding: Finding,
    *,
    iterations: int = 0,
    cost_usd: float = 0.0,
) -> str:
    """
    Persist a Finding to the findings table.

    Args:
        finding:    Validated Finding from the agent loop.
        iterations: Number of loop steps consumed (from run_agent _meta).
        cost_usd:   Spend delta for this agent run (from CostGuard spend file).

    Returns:
        The generated row id (uuid4 string).
    """
    row_id     = str(uuid.uuid4())
    created_at = int(time.time() * 1000)

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO findings
              (id, company_id, created_at, trigger_json, primary_driver,
               hypothesis, evidence_json, confidence, needs_human_review,
               iterations, cost_usd)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row_id,
                finding.ticker,
                created_at,
                json.dumps(finding.trigger),
                finding.primary_driver,
                finding.hypothesis,
                json.dumps(finding.evidence),
                finding.confidence,
                1 if finding.needs_human_review else 0,
                iterations,
                cost_usd,
            ),
        )

    return row_id


def list_findings(limit: int = 50, ticker: str | None = None) -> list[dict]:
    """
    Return findings newest-first as plain dicts with snake_case keys.

    trigger_json and evidence_json are parsed back to Python objects.
    The router layer normalizes keys to camelCase before sending to clients.
    """
    if ticker is not None:
        query  = (
            "SELECT * FROM findings WHERE company_id = ? "
            "ORDER BY created_at DESC LIMIT ?"
        )
        params: tuple = (ticker, limit)
    else:
        query  = "SELECT * FROM findings ORDER BY created_at DESC LIMIT ?"
        params = (limit,)

    with get_connection() as conn:
        rows = conn.execute(query, params).fetchall()

    result = []
    for r in rows:
        result.append({
            "id":                 r["id"],
            "company_id":         r["company_id"],
            "created_at":         r["created_at"],
            "trigger":            json.loads(r["trigger_json"]),
            "primary_driver":     r["primary_driver"],
            "hypothesis":         r["hypothesis"],
            "evidence":           json.loads(r["evidence_json"]),
            "confidence":         r["confidence"],
            "needs_human_review": bool(r["needs_human_review"]),
            "iterations":         r["iterations"],
            "cost_usd":           r["cost_usd"],
        })
    return result
