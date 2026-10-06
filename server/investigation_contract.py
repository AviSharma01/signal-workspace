"""Strict application commands and Finding contract for #34 (not the V1 schema)."""
from typing import Literal

from pydantic import Field, StrictInt, StrictStr

from event_contract import Command

METHOD_VERSION = 'bounded-investigation@1'
VALIDATOR_VERSION = 'finding-validation@1'


class Trigger(Command):
    kind: Literal['event', 'watch_event']
    id: StrictStr = Field(min_length=1)
    active_only: bool = False


class Boundary(Command):
    perspective: Literal['public_information', 'system_observation']
    as_of: StrictInt = Field(ge=0)


class Budgets(Command):
    steps: StrictInt = Field(ge=0)
    elapsed_ms: StrictInt = Field(ge=0)
    model_spend_usd: float | None = Field(default=None, ge=0, allow_inf_nan=False)


class RunCommand(Command):
    trigger: Trigger
    boundary: Boundary
    budgets: Budgets
    mode: Literal['deterministic', 'optional_model'] = 'deterministic'


class FindingCitation(Command):
    evidence_id: StrictStr
    # Exact application-owned provenance, timing and eligibility from the frozen tool.
    reference: dict


class Claim(Command):
    text: StrictStr = Field(min_length=1)
    citations: list[FindingCitation] = Field(min_length=1)


class Finding(Command):
    run_id: StrictStr
    trigger: dict
    boundary: Boundary
    outcome: Literal['unexplained', 'insufficient_eligible_evidence', 'capability_unavailable', 'budget_exhausted']
    summary: StrictStr = Field(min_length=1)
    hypotheses_considered: list[StrictStr]
    claims: list[Claim]
    counterevidence: list[Claim]
    unresolved_questions: list[StrictStr] = Field(min_length=1)
    confidence: Literal['low', 'medium', 'high']
    confidence_basis: StrictStr = Field(min_length=1)
    limitations: list[StrictStr] = Field(min_length=1)
    missingness: list[StrictStr]
    capability_limitations: list[dict]
    method_version: StrictStr
    model_version: StrictStr | None
    review_status: Literal['needs_human_review']
    no_advice_status: Literal['validated']
    advice: None
    created_at: StrictInt = Field(ge=0)
