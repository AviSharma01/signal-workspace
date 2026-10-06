"""Retired V1 eval CLI: cannot invoke a model or display unvalidated Findings."""
from agent.finding import LEGACY_FINDING_DISABLED


def main() -> None:
    raise SystemExit(LEGACY_FINDING_DISABLED)


if __name__ == '__main__':
    main()
