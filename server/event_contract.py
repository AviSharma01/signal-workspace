"""Cited application commands, never model-callable evidence mutations."""

from datetime import date, datetime
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator
from pydantic.alias_generators import to_camel


class Command(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")


def known_timezone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError("timezone must identify a supported IANA calendar zone") from exc


class Citation(Command):
    artifact_version_id: str = Field(min_length=1)
    locator: str = Field(min_length=1, max_length=500)


class Assertion(Command):
    citations: list[Citation] = Field(min_length=1)
    # When the cited assertion itself was publicly available, not its effective date.
    public_at: int | None = Field(default=None, ge=0)
    basis: str = Field(min_length=1, max_length=1000)


class Publication(Assertion):
    kind: Literal["publication"] = "publication"
    artifact_version_id: str
    precision: Literal["exact", "date", "filing_date", "unknown_timezone"]
    raw_value: str = Field(min_length=1)
    timezone: str | None = None

    @model_validator(mode="after")
    def supported_precision(self):
        if self.precision == "exact":
            instant = datetime.fromisoformat(self.raw_value)
            if instant.tzinfo is None or instant.utcoffset() is None:
                raise ValueError("exact publication requires an explicit UTC offset")
        if self.precision in {"date", "filing_date"}:
            date.fromisoformat(self.raw_value)
        if self.precision == "date" and self.timezone is not None:
            known_timezone(self.timezone)
        return self


class Relationship(Assertion):
    kind: Literal["relationship"] = "relationship"
    left_occurrence_id: str
    right_occurrence_id: str
    status: Literal["candidate", "verified", "rejected"]
    counting_ambiguous: bool = True
    # A correction must explicitly identify its original occurrence (left).
    relation: Literal["same_occurrence", "amendment"] = "same_occurrence"


class Identity(Assertion):
    kind: Literal["identity"] = "identity"
    occurrence_id: str
    identity_type: Literal["member", "security"]
    identity_id: str = Field(min_length=1)
    evidence_type: Literal["stable_source_identifier", "verified_cross_source_mapping", "historical_listing"]
    valid_from: date
    valid_to: date | None = None
    listing_id: str | None = None
    calendar_id: str | None = None

    @model_validator(mode="after")
    def historical_scope(self):
        if self.valid_to is not None and self.valid_to <= self.valid_from:
            raise ValueError("identity validity is a nonempty half-open date interval")
        if self.identity_type == "security" and (not self.listing_id or not self.calendar_id):
            raise ValueError("security identity requires historical listing and calendar identity")
        return self


class Fields(Command):
    transaction_direction: Literal["purchase", "sale", "exchange", "unknown"] | None = None
    asset_class: Literal["individual_public_equity", "out_of_scope", "unknown"] | None = None
    transaction_date: date | None = None
    amount_lower: int | None = Field(default=None, ge=0)
    amount_upper: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def amount_range(self):
        if self.amount_lower is not None and self.amount_upper is not None and self.amount_upper < self.amount_lower:
            raise ValueError("amount range must not be reversed")
        return self


class Interpretation(Assertion):
    kind: Literal["interpretation"] = "interpretation"
    occurrence_id: str
    fields: Fields


class Correction(Assertion):
    kind: Literal["correction"] = "correction"
    occurrence_id: str
    fields: Fields
    standing: Literal["supported", "withdrawn", "unresolved"] | None = None
    standing_resolution: Literal["reinstatement", "withdrawal_misattributed"] | None = None

    @model_validator(mode="after")
    def explicit_standing_resolution(self):
        if self.standing_resolution is not None and self.standing != "supported":
            raise ValueError("reinstatement evidence must explicitly support standing")
        return self


class Session(Command):
    session_date: date
    open_at: int = Field(ge=0)
    close_at: int = Field(ge=0)


class Calendar(Assertion):
    kind: Literal["calendar"] = "calendar"
    calendar_id: str = Field(min_length=1)
    timezone: str
    coverage_start: int = Field(ge=0)
    coverage_end: int = Field(ge=0)
    sessions: list[Session]
    # Certification is local to this retained calendar, never provider readiness.
    validation: Literal["validated_complete_regular_sessions"]

    @model_validator(mode="after")
    def session_semantics(self):
        zone = known_timezone(self.timezone)
        if self.coverage_end <= self.coverage_start:
            raise ValueError("calendar coverage must be nonempty")
        ordered = sorted(self.sessions, key=lambda session: session.open_at)
        for index, session in enumerate(ordered):
            if not self.coverage_start <= session.open_at < session.close_at <= self.coverage_end:
                raise ValueError("regular session must lie within certified coverage")
            if datetime.fromtimestamp(session.open_at / 1000, zone).date() != session.session_date:
                raise ValueError("session date must agree with the exchange timezone")
            if index and ordered[index - 1].close_at >= session.open_at:
                raise ValueError("calendar sessions must not overlap or repeat")
        return self


class Context(Assertion):
    kind: Literal["context"] = "context"
    occurrence_id: str
    label: str = Field(min_length=1, max_length=200)


EvidenceAssertion = Annotated[
    Publication | Relationship | Identity | Interpretation | Correction | Calendar | Context,
    Field(discriminator="kind"),
]
ASSERTION_ADAPTER = TypeAdapter(EvidenceAssertion)


class ViewCommand(Command):
    perspective: Literal["public_information", "system_observation"]
    as_of: int = Field(ge=0)
    mode: Literal["historical_recomputation", "corrected_retrospective"] = "historical_recomputation"
    original_as_of: int | None = Field(default=None, ge=0)
    normalization_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def retrospective_boundary(self):
        if self.mode == "corrected_retrospective":
            if self.original_as_of is None or self.original_as_of >= self.as_of:
                raise ValueError("corrected-retrospective requires an explicitly later As-Of boundary")
        elif self.original_as_of is not None:
            raise ValueError("originalAsOf belongs only to corrected-retrospective views")
        return self
