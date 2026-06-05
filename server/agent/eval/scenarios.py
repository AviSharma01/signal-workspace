"""
Declarative scenario specs for the signal investigation agent eval harness.

Each scenario is a plain dict. To add a new scenario: append a dict here.
No other file needs to change.

Fields:
  ticker                   — demo ticker to investigate
  expected_driver          — the known primary_driver the agent must reach
  expected_confidence_band — set of acceptable confidence values
  expected_needs_human_review — expected flag value (bool or None for don't-care)
  scenario_check           — per-scenario rubric check (check #4)
"""

from __future__ import annotations

from agent.eval.rubric import check_drft_evidence, check_nmbs_evidence, check_orch_evidence

SCENARIOS: list[dict] = [
    {
        "ticker": "NMBS",
        "expected_driver": "news",
        "expected_confidence_band": {"high"},
        "expected_needs_human_review": False,
        "scenario_check": check_nmbs_evidence,
    },
    {
        "ticker": "ORCH",
        "expected_driver": "sector",
        "expected_confidence_band": {"medium", "high"},
        "expected_needs_human_review": False,
        "scenario_check": check_orch_evidence,
    },
    {
        "ticker": "DRFT",
        "expected_driver": "unexplained",
        "expected_confidence_band": {"low"},
        "expected_needs_human_review": True,
        "scenario_check": check_drft_evidence,
    },
]
