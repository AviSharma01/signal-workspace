"""
Background scan job for the investigation agent.

Fires every 15 minutes (registered in scheduler.py). Scans the combined
watchlist for anomalous price moves, runs the agent sequentially on each
flagged ticker, and persists each Finding to the findings table.

Per-ticker exceptions are caught so one bad run does not abort the cycle.
CostLimitExceeded aborts the entire cycle cleanly with no partial recovery.
"""

from __future__ import annotations

import json
import logging

from agent.findings_store import insert_finding
from agent.llm.cost_guard import CostLimitExceeded, SPEND_FILE_PATH
from agent.loop import run_agent
from agent.trigger import scan_watchlist
from db.database import SEED_COMPANIES
from seed_demo import DEMO_TICKERS

logger = logging.getLogger(__name__)


def _read_spend() -> float:
    if not SPEND_FILE_PATH.exists():
        return 0.0
    try:
        return float(json.loads(SPEND_FILE_PATH.read_text()).get("total_usd", 0.0))
    except (json.JSONDecodeError, OSError, ValueError):
        return 0.0


def scan_signals() -> None:
    """Scan the watchlist and run the agent on each flagged ticker."""
    n_scanned = len(list(dict.fromkeys(
        [c[0] for c in SEED_COMPANIES] + list(DEMO_TICKERS)
    )))

    flagged = scan_watchlist()
    logger.warning(
        "scan_signals: scanned %d tickers, %d flagged",
        n_scanned, len(flagged),
    )

    if not flagged:
        return

    cycle_cost = 0.0

    for ticker, trigger in flagged:
        spend_before = _read_spend()
        try:
            meta: dict = {}
            finding = run_agent(ticker, trigger, _meta=meta)
            spend_after = _read_spend()
            cost = round(spend_after - spend_before, 6)
            cycle_cost += cost

            insert_finding(
                finding,
                iterations=meta.get("iterations", 0),
                cost_usd=cost,
            )

            logger.warning(
                "scan_signals: %s -> driver=%s confidence=%s cost=$%.4f",
                ticker, finding.primary_driver, finding.confidence, cost,
            )

        except CostLimitExceeded as exc:
            logger.error(
                "scan_signals: CostLimitExceeded — aborting scan cycle: %s", exc
            )
            return

        except Exception as exc:  # noqa: BLE001
            spend_after = _read_spend()
            cost = round(spend_after - spend_before, 6)
            cycle_cost += cost
            logger.error(
                "scan_signals: error on %s (cost=$%.4f): %s",
                ticker, cost, exc,
                exc_info=True,
            )
            continue

    logger.warning("scan_signals: cycle complete — total cost $%.4f", cycle_cost)
