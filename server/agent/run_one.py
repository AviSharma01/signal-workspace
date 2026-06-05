"""
Verification script for slice 4.

Run from server/ as:
    python -m agent.run_one <TICKER>

Looks up the most recent price history for TICKER from the DB, computes the
trigger fields using the same math as seed_demo.py's trigger_check, calls
run_agent, and prints a full diagnostic report.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

# Make `from db.database import ...` work when invoked as python -m agent.run_one
# from inside server/ (same pattern as seed_demo.py and the routers).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.database import get_connection  # noqa: E402
from agent.loop import run_agent  # noqa: E402
from agent.llm.cost_guard import SPEND_FILE_PATH  # noqa: E402


# Mirror seed_demo.py constants exactly.
_N_WINDOW = 30


def _compute_trigger(ticker: str) -> dict:
    """
    Fetch the last N_WINDOW+1 price bars for ticker and compute trigger fields
    using the same math as seed_demo.py's trigger_check function.
    """
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT close, volume FROM price_points "
            "WHERE company_id = ? ORDER BY timestamp DESC LIMIT ?",
            (ticker, _N_WINDOW + 1),
        ).fetchall()

    if len(rows) < 2:
        raise SystemExit(
            f"Not enough price data for {ticker}. "
            "Have you run python seed_demo.py from inside server/?"
        )

    # Rows are newest-first; reverse to chronological order.
    rows = list(reversed(rows))

    closes  = [r["close"]  for r in rows]
    volumes = [r["volume"] for r in rows]

    # Trigger window: last N_WINDOW bars.
    wc = closes[-_N_WINDOW:]
    wv = volumes[-_N_WINDOW:]

    returns   = [wc[i] / wc[i - 1] - 1 for i in range(1, len(wc))]
    mean_r    = sum(returns) / len(returns)
    variance  = sum((r - mean_r) ** 2 for r in returns) / len(returns)
    std_r     = math.sqrt(variance)
    z_score   = (returns[-1] - mean_r) / std_r if std_r != 0 else 0.0

    mean_vol    = sum(wv) / len(wv)
    volume_ratio = wv[-1] / mean_vol if mean_vol != 0 else 0.0

    latest_return = returns[-1]

    return {
        "z_score":           round(z_score, 2),
        "volume_ratio":      round(volume_ratio, 2),
        "direction":         "up" if latest_return > 0 else "down",
        "latest_return_pct": round(latest_return * 100, 2),
    }


def _read_total_spend() -> float:
    """Read the current accumulated spend from the CostGuard file."""
    if not SPEND_FILE_PATH.exists():
        return 0.0
    try:
        data = json.loads(SPEND_FILE_PATH.read_text())
        return float(data.get("total_usd", 0.0))
    except (json.JSONDecodeError, OSError, ValueError):
        return 0.0


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python -m agent.run_one <TICKER>")
        sys.exit(1)

    ticker = sys.argv[1].upper()

    print(f"\n{'=' * 60}")
    print(f"  Investigation: {ticker}")
    print(f"{'=' * 60}")

    trigger = _compute_trigger(ticker)
    print(f"\nTrigger:\n{json.dumps(trigger, indent=2)}")

    spend_before = _read_total_spend()

    meta: dict = {}
    finding = run_agent(ticker, trigger, _meta=meta)

    spend_after = _read_total_spend()
    run_cost    = round(spend_after - spend_before, 6)

    print(f"\nLoop iterations used: {meta.get('iterations', '?')}")

    tool_calls = meta.get("tool_calls", [])
    print(f"\nTool calls ({len(tool_calls)}):")
    for i, tc in enumerate(tool_calls, 1):
        args_str = json.dumps(tc["args"])
        print(f"  {i}. {tc['name']}({args_str})")

    print(f"\nFinding:\n{json.dumps(finding.to_dict(), indent=2)}")

    print(f"\nRun cost: ${run_cost:.6f}  (total accumulated: ${spend_after:.6f})")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
