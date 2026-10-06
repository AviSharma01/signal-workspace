"""Fail-closed compatibility entry point for the retired V1 investigation loop."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agent.finding import Finding, LEGACY_FINDING_DISABLED, LegacyInvestigationDisabled

if TYPE_CHECKING:
    from agent.llm.base import LLMBackend


def run_agent(
    ticker: str,
    trigger: dict[str, Any],
    backend: LLMBackend | None = None,
    max_steps: int = 8,
    _meta: dict[str, Any] | None = None,
) -> Finding:
    """Reject before model construction, tool dispatch or Finding creation."""
    raise LegacyInvestigationDisabled(LEGACY_FINDING_DISABLED)
