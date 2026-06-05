"""
run_agent — the investigation agent loop (§7 of AGENT_SPEC.md).

Drives the LLM through a tool-calling loop until it emits a final Finding,
exhausts the step budget, or a second consecutive validation failure raises.

Hard rules (from server/CLAUDE.md):
- max_steps caps the loop; hitting it returns a forced unexplained Finding.
- Unknown tools and tool exceptions return an error result to the model
  instead of crashing the loop.
- All state flows through `messages`; the loop never opens connections or
  reads env vars itself.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from agent.finding import Finding, validate_finding
from agent.llm.base import LLMBackend, ToolCall
from agent.llm.factory import make_backend
from agent.system_prompt import SYSTEM_PROMPT
from agent.tool_schemas import TOOL_FUNCTIONS, TOOL_SCHEMAS

logger = logging.getLogger(__name__)

_MAX_STEPS = 8


def _assistant_turn(text: str | None, tool_calls: list[ToolCall]) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": text,
        "tool_calls": tool_calls if tool_calls else None,
    }


def _tool_result_turn(tool_call_id: str, content: str) -> dict[str, Any]:
    return {
        "role": "tool",
        "tool_call_id": tool_call_id,
        "content": content,
    }


def _forced_finding(ticker: str, trigger: dict[str, Any]) -> Finding:
    """Returned when the step budget is exhausted without a conclusion."""
    logger.warning("run_agent: step budget exhausted for %s — returning forced finding.", ticker)
    return Finding(
        ticker=ticker,
        trigger=trigger,
        hypothesis="Step budget exhausted; investigation incomplete.",
        primary_driver="unexplained",
        evidence=[],
        confidence="low",
        needs_human_review=True,
        advice=None,
    )


def run_agent(
    ticker: str,
    trigger: dict[str, Any],
    backend: LLMBackend | None = None,
    max_steps: int = _MAX_STEPS,
    _meta: dict[str, Any] | None = None,
) -> Finding:
    """
    Investigate why `ticker` moved.

    Args:
        ticker:    The flagged ticker symbol.
        trigger:   Dict with z_score, volume_ratio, direction, latest_return_pct.
        backend:   LLMBackend to use. Defaults to make_backend() (Anthropic + CostGuard).
        max_steps: Hard cap on loop iterations (governance rule 4).
        _meta:     Optional dict populated with 'iterations' and 'tool_calls' for callers
                   that need to inspect loop behavior (e.g. run_one.py).

    Returns:
        A validated Finding. Never raises on step budget exhaustion.
    """
    if backend is None:
        backend = make_backend()

    if _meta is not None:
        _meta["iterations"] = 0
        _meta["tool_calls"] = []

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                f"{ticker} flagged. Trigger: {json.dumps(trigger)}. "
                "Investigate why it moved. Use the tools."
            ),
        }
    ]

    validation_retries = 0

    for step in range(max_steps):
        if _meta is not None:
            _meta["iterations"] = step + 1

        resp = backend.complete(
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )

        if resp.stop_reason == "end":
            try:
                return validate_finding(resp.text or "")
            except (ValueError, KeyError, TypeError) as exc:
                if validation_retries >= 1:
                    raise
                validation_retries += 1
                logger.warning(
                    "run_agent: validation failed (attempt 1) for %s: %s", ticker, exc
                )
                messages.append(_assistant_turn(resp.text, []))
                messages.append({
                    "role": "user",
                    "content": (
                        f"Your previous output was rejected because: {exc}. "
                        "Return a corrected Finding as plain JSON with no surrounding prose."
                    ),
                })
                continue

        # stop_reason == "tool_use"
        messages.append(_assistant_turn(resp.text, resp.tool_calls))

        for call in resp.tool_calls:
            if _meta is not None:
                _meta["tool_calls"].append({"name": call.name, "args": call.arguments})

            fn = TOOL_FUNCTIONS.get(call.name)
            if fn is None:
                result_str = json.dumps({"error": f"Unknown tool: {call.name}"})
                logger.warning("run_agent: model requested unknown tool %r", call.name)
            else:
                try:
                    result = fn(**call.arguments)
                    result_str = json.dumps(result)
                except Exception as exc:  # noqa: BLE001
                    result_str = json.dumps({"error": str(exc)})
                    logger.warning(
                        "run_agent: tool %r raised: %s", call.name, exc
                    )

            messages.append(_tool_result_turn(call.id, result_str))

    return _forced_finding(ticker, trigger)
