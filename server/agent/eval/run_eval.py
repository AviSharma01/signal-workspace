"""
Eval harness for the signal investigation agent.

Run from server/ as:
    python -m agent.eval.run_eval

Tests the agent end-to-end against the three seeded scenarios (NMBS, ORCH,
DRFT), applies a four-check rubric to each, and prints a pass/fail table.

Exits 0 if all scenarios pass all checks. Exits 1 otherwise (CI-friendly).
Does NOT mock the LLM — every run makes real API calls.
"""

from __future__ import annotations

import json
import math
import sys
import traceback
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from db.database import get_connection           # noqa: E402
from agent.loop import run_agent                  # noqa: E402
from agent.finding import Finding                 # noqa: E402
from agent.llm.cost_guard import SPEND_FILE_PATH  # noqa: E402
from agent.eval.scenarios import SCENARIOS        # noqa: E402
from agent.eval.rubric import run_scenario_checks # noqa: E402

_N_WINDOW = 30


def _compute_trigger(ticker: str) -> dict[str, Any]:
    """Compute trigger fields from DB price history (mirrors run_one.py)."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT close, volume FROM price_points "
            "WHERE company_id = ? ORDER BY timestamp DESC LIMIT ?",
            (ticker, _N_WINDOW + 1),
        ).fetchall()

    if len(rows) < 2:
        raise ValueError(
            f"Not enough price data for {ticker}. "
            "Run 'python seed_demo.py' from inside server/ first."
        )

    rows = list(reversed(rows))
    closes  = [r["close"]  for r in rows]
    volumes = [r["volume"] for r in rows]

    wc = closes[-_N_WINDOW:]
    wv = volumes[-_N_WINDOW:]

    returns  = [wc[i] / wc[i - 1] - 1 for i in range(1, len(wc))]
    mean_r   = sum(returns) / len(returns)
    variance = sum((r - mean_r) ** 2 for r in returns) / len(returns)
    std_r    = math.sqrt(variance)
    z_score  = (returns[-1] - mean_r) / std_r if std_r != 0 else 0.0

    mean_vol     = sum(wv) / len(wv)
    volume_ratio = wv[-1] / mean_vol if mean_vol != 0 else 0.0
    latest_return = returns[-1]

    return {
        "z_score":           round(z_score, 2),
        "volume_ratio":      round(volume_ratio, 2),
        "direction":         "up" if latest_return > 0 else "down",
        "latest_return_pct": round(latest_return * 100, 2),
    }


def _read_spend() -> float:
    if not SPEND_FILE_PATH.exists():
        return 0.0
    try:
        return float(json.loads(SPEND_FILE_PATH.read_text()).get("total_usd", 0.0))
    except (json.JSONDecodeError, OSError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Table rendering
# ---------------------------------------------------------------------------

_COL_W = 82   # total header width

_HEADER = (
    f"{'ticker':<7} {'driver':<13} {'conf':<7} {'iters':<6} "
    f"{'tools':<6} {'cost':>8}   "
    f"{'drvr':>4} {'conf':>4} {'bndy':>4} {'evid':>4}   {'result'}"
)


def _mark(checks: list[tuple[str, bool, str]], name: str) -> str:
    for n, passed, _ in checks:
        if n == name:
            return "✓" if passed else "✗"
    return "?"


def _print_table(results: list[dict]) -> None:
    sep = "─" * len(_HEADER)
    print(f"\n{sep}")
    print(_HEADER)
    print(sep)

    for r in results:
        ticker = r["ticker"]
        if r["error"]:
            print(
                f"{ticker:<7} {'ERROR':<13} {'?':<7} {'?':<6} {'?':<6} "
                f"${r['cost']:>7.4f}   {'✗':>4} {'✗':>4} {'✗':>4} {'✗':>4}   FAIL ✗"
            )
            continue

        f: Finding = r["finding"]
        m: dict   = r["meta"]
        chk       = r["checks"]
        overall   = "PASS ✓" if r["all_passed"] else "FAIL ✗"

        print(
            f"{ticker:<7} {f.primary_driver:<13} {f.confidence:<7} "
            f"{m.get('iterations', '?'):<6} {len(m.get('tool_calls', [])):<6} "
            f"${r['cost']:>7.4f}   "
            f"{_mark(chk, 'correct_driver'):>4} "
            f"{_mark(chk, 'confidence_in_band'):>4} "
            f"{_mark(chk, 'boundary_respected'):>4} "
            f"{_mark(chk, 'scenario_evidence'):>4}   {overall}"
        )

    print(sep)


def _print_failures(results: list[dict]) -> None:
    for r in results:
        ticker = r["ticker"]

        if r["error"]:
            print(f"\n{'─' * 60}")
            print(f"  CRASH: {ticker}")
            print(f"{'─' * 60}")
            print(r["error"])
            continue

        failed = [(n, d) for n, passed, d in r["checks"] if not passed]
        if not failed:
            continue

        print(f"\n{'─' * 60}")
        print(f"  FAILURES: {ticker}")
        print(f"{'─' * 60}")

        for name, detail in failed:
            print(f"\n  [✗] {name}")
            print(f"      {detail}")

        f: Finding = r["finding"]
        m: dict   = r["meta"]

        print(f"\n  Finding:")
        print(f"    primary_driver:     {f.primary_driver}")
        print(f"    confidence:         {f.confidence}")
        print(f"    needs_human_review: {f.needs_human_review}")
        print(f"    advice:             {f.advice}")
        print(f"    hypothesis:         {f.hypothesis[:120]!r}")
        print(f"    evidence ({len(f.evidence)} entries):")
        for e in f.evidence:
            print(f"      {e}")

        calls = m.get("tool_calls", [])
        print(f"\n  Tool trace ({len(calls)} calls):")
        for i, tc in enumerate(calls, 1):
            print(f"    {i}. {tc['name']}({json.dumps(tc['args'])})")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"\n{'═' * _COL_W}")
    print("  Signal Investigation Agent — Eval Harness")
    print(f"{'═' * _COL_W}\n")

    results: list[dict] = []

    for scenario in SCENARIOS:
        ticker = scenario["ticker"]
        print(f"  Running {ticker} ...", end=" ", flush=True)

        spend_before = _read_spend()
        try:
            trigger = _compute_trigger(ticker)
            meta: dict = {}
            finding = run_agent(ticker, trigger, _meta=meta)
            spend_after = _read_spend()
            cost = round(spend_after - spend_before, 6)

            checks    = run_scenario_checks(finding, scenario, meta)
            all_passed = all(p for _, p, _ in checks)

            results.append({
                "ticker":     ticker,
                "finding":    finding,
                "meta":       meta,
                "checks":     checks,
                "all_passed": all_passed,
                "cost":       cost,
                "error":      None,
            })
            print("PASS ✓" if all_passed else "FAIL ✗", f"  (${cost:.4f})")

        except Exception:  # noqa: BLE001
            spend_after = _read_spend()
            cost = round(spend_after - spend_before, 6)
            results.append({
                "ticker":     ticker,
                "finding":    None,
                "meta":       {},
                "checks":     [],
                "all_passed": False,
                "cost":       cost,
                "error":      traceback.format_exc(),
            })
            print(f"ERROR  (${cost:.4f})")

    _print_table(results)
    _print_failures(results)

    passed      = sum(1 for r in results if r["all_passed"])
    total       = len(results)
    total_cost  = sum(r["cost"] for r in results)

    print(f"\n{'═' * _COL_W}")
    print(f"  {passed}/{total} scenarios passed   total cost ${total_cost:.4f}")
    print(f"{'═' * _COL_W}\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
