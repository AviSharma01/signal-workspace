"""Disabled V1 persistence/display paths. Retained rows are not V2 Findings."""
from agent.finding import Finding, LEGACY_FINDING_DISABLED, LegacyInvestigationDisabled


def insert_finding(
    finding: Finding,
    *,
    iterations: int = 0,
    cost_usd: float = 0.0,
) -> str:
    raise LegacyInvestigationDisabled(LEGACY_FINDING_DISABLED)


def list_findings(limit: int = 50, ticker: str | None = None) -> list[dict]:
    raise LegacyInvestigationDisabled(LEGACY_FINDING_DISABLED)
