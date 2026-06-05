"""
POST /api/scan/run — DEBUG SURFACE ONLY.

Triggers one scan cycle synchronously and returns the IDs of any Findings
produced. This exists so a reviewer can see a Finding appear on the detail
page in real time without waiting 15 minutes for the scheduled job.

This is NOT a product feature. The scheduled job in jobs/scan_signals.py is
the real autonomy story. Do not expose this route to untrusted callers.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter

from agent.findings_store import insert_finding
from agent.llm.cost_guard import CostLimitExceeded, SPEND_FILE_PATH
from agent.loop import run_agent
from agent.trigger import scan_watchlist
from db.database import SEED_COMPANIES
from seed_demo import DEMO_TICKERS

router = APIRouter(prefix="/api")

logger = logging.getLogger(__name__)


def _read_spend() -> float:
    if not SPEND_FILE_PATH.exists():
        return 0.0
    try:
        return float(json.loads(SPEND_FILE_PATH.read_text()).get("total_usd", 0.0))
    except (json.JSONDecodeError, OSError, ValueError):
        return 0.0


@router.post("/scan/run")
def run_scan() -> dict:
    """Run one scan cycle and return summary + generated finding ids."""
    watchlist = list(dict.fromkeys(
        [c[0] for c in SEED_COMPANIES] + list(DEMO_TICKERS)
    ))
    n_scanned = len(watchlist)

    flagged = scan_watchlist()
    finding_ids: list[str] = []

    for ticker, trigger in flagged:
        spend_before = _read_spend()
        try:
            meta: dict = {}
            finding = run_agent(ticker, trigger, _meta=meta)
            spend_after = _read_spend()
            cost = round(spend_after - spend_before, 6)

            row_id = insert_finding(
                finding,
                iterations=meta.get("iterations", 0),
                cost_usd=cost,
            )
            finding_ids.append(row_id)

            logger.warning(
                "scan/run: %s -> driver=%s confidence=%s cost=$%.4f",
                ticker, finding.primary_driver, finding.confidence, cost,
            )

        except CostLimitExceeded as exc:
            logger.error("scan/run: CostLimitExceeded — aborting: %s", exc)
            break

        except Exception as exc:  # noqa: BLE001
            logger.error("scan/run: error on %s: %s", ticker, exc, exc_info=True)
            continue

    return {
        "scanned": n_scanned,
        "flagged": len(flagged),
        "findings": finding_ids,
    }
