"""
Finding dataclass and validate_finding — the output contract for the
investigation agent (§6 of AGENT_SPEC.md).

validate_finding enforces the governance contract in code, not just prompt.
The validator is the guarantee; the prompt is guidance.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

_VALID_PRIMARY_DRIVERS = {"news", "discussion", "sector", "unexplained"}
_VALID_CONFIDENCE      = {"high", "medium", "low"}

_REQUIRED_FIELDS: list[tuple[str, type]] = [
    ("ticker",            str),
    ("trigger",           dict),
    ("hypothesis",        str),
    ("primary_driver",    str),
    ("evidence",          list),
    ("confidence",        str),
    ("needs_human_review", bool),
    # advice is validated separately (must be None/null)
]


@dataclass
class Finding:
    ticker: str
    trigger: dict[str, Any]
    hypothesis: str
    primary_driver: str
    evidence: list[dict[str, Any]]
    confidence: str
    needs_human_review: bool
    advice: None = field(default=None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ticker": self.ticker,
            "trigger": self.trigger,
            "hypothesis": self.hypothesis,
            "primary_driver": self.primary_driver,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "needs_human_review": self.needs_human_review,
            "advice": self.advice,
        }


def _strip_markdown(text: str) -> str:
    """Strip ```json ... ``` or ``` ... ``` fences if the model wraps its output."""
    text = text.strip()
    fenced = re.match(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL)
    if fenced:
        return fenced.group(1).strip()
    return text


def validate_finding(text: str) -> Finding:
    """
    Parse the model's JSON output and enforce the governance contract.

    Checks (in order):
      1. Valid JSON parseable as a dict.
      2. All required fields present with correct types.
      3. primary_driver ∈ {news, discussion, sector, unexplained}.
      4. confidence ∈ {high, medium, low}.
      5. advice is exactly None/null — non-null is a hard rejection (§5, rule 3).
      6. confidence == "low" forces needs_human_review = True (override + log).
      7. evidence is a list.

    Raises ValueError with a clear message on any failure so the loop can
    send a corrective prompt back to the model.
    """
    # 1. Parse JSON
    try:
        raw: Any = json.loads(_strip_markdown(text))
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Output is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"Expected a JSON object, got {type(raw).__name__}")

    # 2. Required fields and types
    for field_name, expected_type in _REQUIRED_FIELDS:
        if field_name not in raw:
            raise ValueError(f"Missing required field: '{field_name}'")
        val = raw[field_name]
        if not isinstance(val, expected_type):
            raise ValueError(
                f"Field '{field_name}' must be {expected_type.__name__}, "
                f"got {type(val).__name__}"
            )

    # Advice must be present (key check) before the null enforcement below.
    if "advice" not in raw:
        raise ValueError("Missing required field: 'advice'")

    # 3. primary_driver enum
    pd = raw["primary_driver"]
    if pd not in _VALID_PRIMARY_DRIVERS:
        raise ValueError(
            f"primary_driver must be one of {sorted(_VALID_PRIMARY_DRIVERS)}, got {pd!r}"
        )

    # 4. confidence enum
    conf = raw["confidence"]
    if conf not in _VALID_CONFIDENCE:
        raise ValueError(
            f"confidence must be one of {sorted(_VALID_CONFIDENCE)}, got {conf!r}"
        )

    # 5. advice MUST be null — hard rejection, no override
    if raw["advice"] is not None:
        raise ValueError(
            "advice must be null. The agent must never emit recommendations, "
            "price targets, or buy/sell/hold language."
        )

    # 6. low confidence forces needs_human_review
    needs_review: bool = raw["needs_human_review"]
    if conf == "low" and not needs_review:
        logger.warning(
            "validate_finding: confidence='low' but needs_human_review=false — "
            "overriding to true per governance contract."
        )
        needs_review = True

    # 7. evidence is a list (already checked by type check above)

    return Finding(
        ticker=raw["ticker"],
        trigger=raw["trigger"],
        hypothesis=raw["hypothesis"],
        primary_driver=pd,
        evidence=raw["evidence"],
        confidence=conf,
        needs_human_review=needs_review,
        advice=None,
    )
