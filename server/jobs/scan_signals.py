"""Retired V1 scan: cannot scan, create Findings or write to the legacy store."""
from agent.finding import LEGACY_FINDING_DISABLED, LegacyInvestigationDisabled


def scan_signals() -> None:
    raise LegacyInvestigationDisabled(LEGACY_FINDING_DISABLED)


if __name__ == '__main__':
    scan_signals()
