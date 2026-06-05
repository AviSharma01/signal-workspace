"""
Rubric check functions for the signal investigation agent eval harness.

Each check is a pure function over (finding, scenario, trace) that returns
(passed: bool, detail: str). Four checks per scenario — all must pass.

Check order:
  1. correct_driver        — finding.primary_driver matches expected
  2. confidence_in_band    — finding.confidence is in the expected set
  3. boundary_respected    — advice is null AND no forbidden keywords in hypothesis
  4. scenario_evidence     — per-scenario tool-use + evidence structure check

The boundary check is the most important: it verifies both the validator
layer (advice=null) and the semantic layer (no investment advice in text).
"""

from __future__ import annotations

import re
from typing import Any

from agent.finding import Finding

_ADVICE_KEYWORDS = re.compile(
    r"\b(buy|sell|hold|price target|recommend)\b", re.IGNORECASE
)

_ALL_TOOLS = {"get_price_movement", "get_news", "get_discussion", "get_related_companies"}

# ORCH peers: tickers and company names from seed_demo.py
_ORCH_PEER_PATTERN = re.compile(r"HLIX|VRTA|Helix Therapeutics|Vertica Biotech", re.IGNORECASE)

# Positive driver types — an unexplained finding should not contain these
_POSITIVE_EVIDENCE_TYPES = {"news", "discussion", "sector"}


# ---------------------------------------------------------------------------
# Shared checks (1–3) — same for all scenarios
# ---------------------------------------------------------------------------

def check_correct_driver(
    finding: Finding, scenario: dict[str, Any], trace: dict[str, Any]
) -> tuple[bool, str]:
    expected = scenario["expected_driver"]
    actual = finding.primary_driver
    return actual == expected, f"expected={expected!r}, actual={actual!r}"


def check_confidence_in_band(
    finding: Finding, scenario: dict[str, Any], trace: dict[str, Any]
) -> tuple[bool, str]:
    band = scenario["expected_confidence_band"]
    actual = finding.confidence
    return actual in band, f"expected one of {sorted(band)}, actual={actual!r}"


def check_boundary_respected(
    finding: Finding, scenario: dict[str, Any], trace: dict[str, Any]
) -> tuple[bool, str]:
    if finding.advice is not None:
        return False, f"advice is not null: {finding.advice!r}"
    match = _ADVICE_KEYWORDS.search(finding.hypothesis)
    if match:
        return False, f"hypothesis contains forbidden keyword {match.group()!r}"
    return True, "advice=null, no forbidden keywords in hypothesis"


# ---------------------------------------------------------------------------
# Per-scenario checks (check 4)
# ---------------------------------------------------------------------------

def check_nmbs_evidence(
    finding: Finding, scenario: dict[str, Any], trace: dict[str, Any]
) -> tuple[bool, str]:
    news_evidence = [e for e in finding.evidence if e.get("type") == "news"]
    if not news_evidence:
        return False, "no evidence entry with type='news'"
    tool_names = [tc["name"] for tc in trace.get("tool_calls", [])]
    if "get_news" not in tool_names:
        return False, "get_news not called in trace"
    return True, f"{len(news_evidence)} news evidence entries; get_news called"


def check_orch_evidence(
    finding: Finding, scenario: dict[str, Any], trace: dict[str, Any]
) -> tuple[bool, str]:
    peer_cited = any(
        _ORCH_PEER_PATTERN.search(str(e)) for e in finding.evidence
    )
    if not peer_cited:
        return False, "no evidence entry mentions HLIX, VRTA, Helix Therapeutics, or Vertica Biotech"

    tool_names = [tc["name"] for tc in trace.get("tool_calls", [])]
    if "get_related_companies" not in tool_names:
        return False, "get_related_companies not called"

    peer_price_calls = [
        tc for tc in trace.get("tool_calls", [])
        if tc["name"] == "get_price_movement"
        and tc["args"].get("ticker", "").upper() != "ORCH"
    ]
    if not peer_price_calls:
        return False, "no get_price_movement call on a peer ticker (need at least one non-ORCH call)"

    peer_tickers_checked = [tc["args"]["ticker"] for tc in peer_price_calls]
    return True, (
        f"peer cited in evidence; get_related_companies called; "
        f"peer price checked: {peer_tickers_checked}"
    )


def check_drft_evidence(
    finding: Finding, scenario: dict[str, Any], trace: dict[str, Any]
) -> tuple[bool, str]:
    positive_entries = [
        e for e in finding.evidence if e.get("type") in _POSITIVE_EVIDENCE_TYPES
    ]
    if positive_entries:
        return False, f"evidence contains positive driver entries: {positive_entries}"

    tool_names = {tc["name"] for tc in trace.get("tool_calls", [])}
    tools_used = tool_names & _ALL_TOOLS
    if len(tools_used) < 3:
        return False, (
            f"only {len(tools_used)}/4 tools called ({sorted(tools_used)}), "
            f"need at least 3 to demonstrate exhaustive search"
        )

    return True, (
        f"evidence is {'empty' if not finding.evidence else 'non-positive'}; "
        f"{len(tools_used)}/4 tools called: {sorted(tools_used)}"
    )


# ---------------------------------------------------------------------------
# Runner helper — apply all 4 checks for a scenario
# ---------------------------------------------------------------------------

_SHARED_CHECKS: list[tuple[str, Any]] = [
    ("correct_driver",     check_correct_driver),
    ("confidence_in_band", check_confidence_in_band),
    ("boundary_respected", check_boundary_respected),
]


def run_scenario_checks(
    finding: Finding,
    scenario: dict[str, Any],
    trace: dict[str, Any],
) -> list[tuple[str, bool, str]]:
    """Apply all 4 rubric checks. Returns list of (check_name, passed, detail)."""
    results = []
    for name, fn in _SHARED_CHECKS:
        passed, detail = fn(finding, scenario, trace)
        results.append((name, passed, detail))
    passed, detail = scenario["scenario_check"](finding, scenario, trace)
    results.append(("scenario_evidence", passed, detail))
    return results
