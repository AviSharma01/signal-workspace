"""
CostGuard — wraps any LLMBackend and enforces a hard spend cap.

Persists a running USD total to .agent_spend.json so it survives restarts.
Writes are atomic (write to temp file, os.replace) so a crash mid-write
cannot corrupt the file.

Prices for claude-sonnet-4-6, read from:
  https://platform.claude.com/docs/en/docs/about-claude/models/overview
  on 2026-06-04
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.llm.base import LLMBackend, LLMResponse

# Per-token prices for claude-sonnet-4-6 (USD).
# Source: https://platform.claude.com/docs/en/docs/about-claude/models/overview
# Read: 2026-06-04  — update these constants when switching models.
SONNET_4_6_INPUT_PRICE_PER_TOKEN  = 3.00  / 1_000_000   # $3.00 / MTok
SONNET_4_6_OUTPUT_PRICE_PER_TOKEN = 15.00 / 1_000_000   # $15.00 / MTok

SOFT_WARN = 40.0   # USD — loud warning, call still goes through
HARD_CAP  = 50.0   # USD — raises CostLimitExceeded before calling the API

SPEND_FILE_PATH = Path(__file__).resolve().parent.parent.parent / ".agent_spend.json"


class CostLimitExceeded(Exception):
    """Raised when accumulated spend reaches HARD_CAP before a call is made."""


class CostGuard(LLMBackend):
    """Wraps an LLMBackend, tracking cumulative spend and enforcing caps."""

    def __init__(
        self,
        backend: LLMBackend,
        input_price_per_token: float = SONNET_4_6_INPUT_PRICE_PER_TOKEN,
        output_price_per_token: float = SONNET_4_6_OUTPUT_PRICE_PER_TOKEN,
        spend_file: Path = SPEND_FILE_PATH,
    ) -> None:
        self._backend = backend
        self._input_price = input_price_per_token
        self._output_price = output_price_per_token
        self._path = spend_file
        self._state: dict[str, Any] = self._load()

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def complete(self, *, system: str, messages: list[dict],
                 tools: list[dict]) -> LLMResponse:
        total = self._state["total_usd"]

        if total >= HARD_CAP:
            raise CostLimitExceeded(
                f"Accumulated spend ${total:.4f} has reached the hard cap "
                f"${HARD_CAP:.2f}. No further API calls will be made."
            )

        if total >= SOFT_WARN:
            print(
                f"\n⚠️  WARNING: agent spend ${total:.4f} is approaching the "
                f"hard cap ${HARD_CAP:.2f}. Review usage before continuing.\n"
            )

        response = self._backend.complete(system=system, messages=messages, tools=tools)
        self._record(response)
        return response

    def state(self) -> dict[str, Any]:
        """Return a copy of the current persisted state (total + call log)."""
        return dict(self._state)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> dict[str, Any]:
        if self._path.exists():
            try:
                return json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {"total_usd": 0.0, "calls": []}

    def _save(self) -> None:
        """Atomic write: temp file + os.replace (POSIX-atomic)."""
        fd, tmp_path = tempfile.mkstemp(
            dir=self._path.parent, prefix=".agent_spend_", suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(self._state, f, indent=2)
            os.replace(tmp_path, self._path)
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

    def _record(self, response: LLMResponse) -> None:
        usage = response.usage or {}
        input_tokens  = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)
        call_cost = (
            input_tokens  * self._input_price +
            output_tokens * self._output_price
        )

        self._state["total_usd"] = round(
            self._state["total_usd"] + call_cost, 8
        )
        self._state["calls"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(call_cost, 8),
        })
        self._save()
