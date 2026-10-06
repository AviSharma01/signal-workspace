"""Retired V1 CLI: cannot compute triggers, invoke a model or display Findings."""
from agent.finding import LEGACY_FINDING_DISABLED


def main() -> None:
    raise SystemExit(LEGACY_FINDING_DISABLED)


if __name__ == '__main__':
    main()
