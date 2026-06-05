"""
Slice-3 verification — run from inside server/:
    python -m agent.llm.test_call

Makes one trivial call through the factory-built backend and prints the
cost-guard state before and after.
"""

import json
import sys
from pathlib import Path

from agent.llm.cost_guard import SPEND_FILE_PATH
from agent.llm.factory import make_backend


def _read_spend_file() -> dict:
    if SPEND_FILE_PATH.exists():
        return json.loads(SPEND_FILE_PATH.read_text())
    return {"total_usd": 0.0, "calls": []}


def main() -> None:
    # --- state before ---
    before = _read_spend_file()
    print("=" * 60)
    print("COST GUARD STATE — BEFORE CALL")
    print("=" * 60)
    print(f"  Spend file : {SPEND_FILE_PATH}")
    print(f"  Total USD  : ${before['total_usd']:.6f}")
    print(f"  Calls so far: {len(before['calls'])}")

    # --- build backend (the only place that constructs it) ---
    backend = make_backend("anthropic")

    # --- make one trivial call ---
    print()
    print("Making call...")
    response = backend.complete(
        system="You are a helpful test assistant. Reply briefly.",
        messages=[{"role": "user", "content": "Say 'cost guard test ok' and nothing else."}],
        tools=[],
    )

    # --- print response ---
    print()
    print("=" * 60)
    print("RESPONSE")
    print("=" * 60)
    print(f"  Text       : {response.text!r}")
    print(f"  Stop reason: {response.stop_reason}")
    print(f"  Tool calls : {response.tool_calls}")

    # --- token counts and computed cost ---
    usage = response.usage or {}
    input_tokens  = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    from agent.llm.cost_guard import (
        SONNET_4_6_INPUT_PRICE_PER_TOKEN,
        SONNET_4_6_OUTPUT_PRICE_PER_TOKEN,
    )
    call_cost = (
        input_tokens  * SONNET_4_6_INPUT_PRICE_PER_TOKEN +
        output_tokens * SONNET_4_6_OUTPUT_PRICE_PER_TOKEN
    )

    print()
    print("=" * 60)
    print("USAGE & COST")
    print("=" * 60)
    print(f"  Input tokens : {input_tokens}")
    print(f"  Output tokens: {output_tokens}")
    print(f"  Call cost    : ${call_cost:.6f}")

    # --- state after ---
    after = _read_spend_file()
    last_entry = after["calls"][-1] if after["calls"] else None

    print()
    print("=" * 60)
    print("COST GUARD STATE — AFTER CALL")
    print("=" * 60)
    print(f"  Spend file : {SPEND_FILE_PATH}")
    print(f"  Total USD  : ${after['total_usd']:.6f}")
    print(f"  Calls so far: {len(after['calls'])}")
    print(f"  Last entry :")
    if last_entry:
        for k, v in last_entry.items():
            print(f"    {k}: {v}")
    else:
        print("    (none — spend file was not updated; this is a FAILURE)")
        sys.exit(1)

    # Sanity check: the file was actually updated
    if after["total_usd"] <= before["total_usd"] and len(after["calls"]) <= len(before["calls"]):
        print()
        print("FAILURE: spend file was not updated after the call.")
        sys.exit(1)

    print()
    print("All checks passed.")


if __name__ == "__main__":
    main()
