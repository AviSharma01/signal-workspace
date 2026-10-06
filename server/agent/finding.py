"""Disabled V1 output contract; only the #34 application may validate Findings."""

LEGACY_FINDING_DISABLED = (
    'Legacy V1 investigations are disabled. Use the V2 InvestigationApplication '
    'with an Event/Watch Event, declared As-Of boundary and eligible evidence.'
)


class LegacyInvestigationDisabled(RuntimeError):
    """A legacy caller attempted to bypass the application-owned V2 boundary."""


class Finding:
    """Compatibility name that cannot construct or serialize a legacy Finding."""

    def __init__(self, *args, **kwargs):
        raise LegacyInvestigationDisabled(LEGACY_FINDING_DISABLED)

    def to_dict(self) -> dict:
        raise LegacyInvestigationDisabled(LEGACY_FINDING_DISABLED)


def validate_finding(text: str) -> Finding:
    raise LegacyInvestigationDisabled(LEGACY_FINDING_DISABLED)
