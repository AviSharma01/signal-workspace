from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, Literal

from market_conformance import production_market_readiness


CAPABILITY_CONTRACT_VERSION = "signal-capabilities@1"

Availability = Literal["available", "conditional", "unavailable"]
ResultState = Literal["empty", "stale", "partial", "error", "successful"]

MARKET_PREREQUISITES = [
    "approved_market_data_provider",
    "validated_historical_coverage_and_retention",
    "validated_identity_and_listing_joins",
    "validated_session_calendar_and_timezone_semantics",
    "validated_ohlcv_corporate_action_currency_and_unit_semantics",
    "retained_provenance_and_revision_snapshots",
    "validated_daily_acquisition_catch_up_and_gap_handling",
    "independent_numerical_correctness_and_workload_evidence",
]


def capability_state(
    capability_id: str,
    name: str,
    availability: Availability,
    detail: str,
    governing_version: str,
    *,
    evaluated_at: int,
    reason_codes: list[str] | None = None,
    unmet_prerequisites: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "id": capability_id,
        "name": name,
        "availability": availability,
        "reason_codes": reason_codes or [],
        "detail": detail,
        "evaluated_at": evaluated_at,
        "governing_version": governing_version,
        "unmet_prerequisites": unmet_prerequisites or [],
    }


def result_state(state: ResultState, detail: str, *, evaluated_at: int) -> dict[str, Any]:
    return {"state": state, "detail": detail, "evaluated_at": evaluated_at}


def market_unavailable(
    capability_id: str,
    name: str,
    detail: str,
    *,
    evaluated_at: int,
    extra_reason_codes: list[str] | None = None,
    extra_prerequisites: list[str] | None = None,
) -> dict[str, Any]:
    prerequisites = [*MARKET_PREREQUISITES, *(extra_prerequisites or [])]
    return capability_state(
        capability_id,
        name,
        "unavailable",
        detail,
        "signal-v2-market-data-contract@1",
        evaluated_at=evaluated_at,
        reason_codes=["market_data_contract_unsatisfied", *(extra_reason_codes or [])],
        unmet_prerequisites=[
            *[{"code": code, "detail": code.replace("_", " ")} for code in prerequisites],
            *production_market_readiness(evaluated_at=evaluated_at)["unmet_prerequisites"],
        ],
    )


def market_outcomes_capability(*, evaluated_at: int) -> dict[str, Any]:
    return market_unavailable(
        "market.outcomes",
        "Production market outcomes",
        "No production market-data provider or compatible fallback is approved.",
        evaluated_at=evaluated_at,
    )


class CapabilityApplication:
    def __init__(
        self,
        readiness_provider: Callable[[], dict[str, Any]],
        clock: Callable[[], int] | None = None,
    ) -> None:
        self._readiness_provider = readiness_provider
        self._clock = clock or (lambda: int(time.time() * 1000))

    def query(self) -> dict[str, Any]:
        evaluated_at = self._clock()
        readiness = self._readiness_provider()
        chamber_states = [readiness["house"], readiness["senate"]]
        chamber_capabilities = [
            {
                "id": f"disclosure.{item['chamber']}",
                "name": f"{item['chamber'].title()} disclosure readiness",
                "availability": item["availability"],
                "reason_codes": item["reason_codes"],
                "detail": item["detail"],
                "evaluated_at": item["evaluated_at"],
                "governing_version": item["governing_version"],
                "unmet_prerequisites": item["unmet_prerequisites"],
            }
            for item in chamber_states
        ]
        chamber_prerequisites = [
            {
                "code": f"{item['chamber']}_disclosure_readiness",
                "detail": f"{item['chamber'].title()} readiness is {item['availability']}",
            }
            for item in chamber_states
            if item["availability"] != "available"
        ]
        if any(item["availability"] == "available" for item in chamber_states):
            disclosure_availability: Availability = "available"
            disclosure_reason_codes = (
                ["limited_chamber_coverage"] if chamber_prerequisites else []
            )
            disclosure_detail = (
                "At least one chamber passed every readiness gate; coverage remains explicitly chamber-scoped."
            )
        elif any(item["availability"] == "conditional" for item in chamber_states):
            disclosure_availability = "conditional"
            disclosure_reason_codes = ["chamber_readiness_conditional"]
            disclosure_detail = (
                "At least one chamber is conditionally ready, but partial readiness does not activate dependent work."
            )
        else:
            disclosure_availability = "unavailable"
            disclosure_reason_codes = ["chamber_readiness_unavailable"]
            disclosure_detail = "No chamber has passed every approved disclosure-source readiness gate."

        capabilities = [
            production_market_readiness(evaluated_at=evaluated_at),
            capability_state(
                "disclosure.evidence_retention",
                "Disclosure evidence retention",
                "available",
                "Retained source evidence and retrieval history can be inspected through application APIs.",
                "signal-v2-evidence-spine@1",
                evaluated_at=evaluated_at,
            ),
            *chamber_capabilities,
            capability_state(
                "events.derivation",
                "Event derivation",
                "available",
                "Occurrence-level Events and use-specific eligibility can be derived from retained evidence.",
                "event-pit@1",
                evaluated_at=evaluated_at,
            ),
            capability_state(
                "monitoring.watch_lifecycle",
                "Watch Event lifecycle",
                "available",
                "Eligible Events can be admitted and reevaluated independently of market data.",
                "watch-lifecycle@1",
                evaluated_at=evaluated_at,
            ),
            capability_state(
                "monitoring.disclosure_discovery",
                "Disclosure discovery monitoring",
                disclosure_availability,
                disclosure_detail,
                "signal-v2-disclosure-readiness-v1",
                evaluated_at=evaluated_at,
                reason_codes=disclosure_reason_codes,
                unmet_prerequisites=chamber_prerequisites,
            ),
            capability_state(
                "analysis.disclosure_coverage",
                "Disclosure-only Analysis coverage",
                disclosure_availability,
                disclosure_detail,
                "signal-v2-analysis@1",
                evaluated_at=evaluated_at,
                reason_codes=disclosure_reason_codes,
                unmet_prerequisites=chamber_prerequisites,
            ),
            market_unavailable(
                "analysis.market_event_study",
                "Market-dependent Analysis",
                "Historical event studies and benchmark-adjusted outcomes are unavailable until the market-data contract passes.",
                evaluated_at=evaluated_at,
            ),
            market_outcomes_capability(evaluated_at=evaluated_at),
            market_unavailable(
                "monitoring.market_checks",
                "Market-dependent Monitoring checks",
                "Price, volume, return, volatility, and benchmark checks are unavailable.",
                evaluated_at=evaluated_at,
            ),
            market_unavailable(
                "monitoring.market_anomaly_detection",
                "Market anomaly detection",
                "Market anomaly detection is unavailable until market readiness passes and deterministic thresholds are approved.",
                evaluated_at=evaluated_at,
                extra_reason_codes=["market_anomaly_thresholds_not_approved"],
                extra_prerequisites=["approved_deterministic_market_anomaly_thresholds"],
            ),
        ]

        for consensus_id, name in (
            ("raw", "Historical Raw Consensus"),
            ("expected", "Historical Expected Consensus"),
            ("excess", "Historical Excess Consensus"),
        ):
            capabilities.append(
                capability_state(
                    f"analysis.consensus.{consensus_id}",
                    name,
                    "unavailable",
                    f"{name} is deferred after bounded evidence attempts did not establish computability.",
                    "signal-v2-consensus-decision@1",
                    evaluated_at=evaluated_at,
                    reason_codes=["consensus_deferred_unsupported_evidence"],
                    unmet_prerequisites=[
                        {
                            "code": "approved_supported_consensus_evidence_and_method",
                            "detail": "A separately approved evidence-backed activation is required.",
                        }
                    ],
                )
            )

        capabilities.extend(
            [
                capability_state(
                    "investigation.runtime",
                    "V2 investigation runtime",
                    "unavailable",
                    "The bounded V2 investigation runtime belongs to #34 and is not implemented by this slice.",
                    "signal-v2-investigation-contract@1",
                    evaluated_at=evaluated_at,
                    reason_codes=["investigation_runtime_not_implemented"],
                    unmet_prerequisites=[
                        {
                            "code": "bounded_investigation_runtime",
                            "detail": "Implement the #34 bounded, read-only, validated investigation runtime.",
                        }
                    ],
                ),
                market_unavailable(
                    "investigation.market_triggered",
                    "Market-triggered investigation",
                    "Market-triggered investigation requires both market readiness and the bounded V2 investigation runtime.",
                    evaluated_at=evaluated_at,
                    extra_reason_codes=["investigation_runtime_not_implemented"],
                    extra_prerequisites=["bounded_investigation_runtime"],
                ),
                capability_state(
                    "investigation.selection_evaluation",
                    "Investigation-selection evaluation",
                    "unavailable",
                    "No defensible independent target and declared baseline are currently implemented.",
                    "signal-v2-investigation-evaluation@1",
                    evaluated_at=evaluated_at,
                    reason_codes=["independent_evaluation_target_unavailable"],
                    unmet_prerequisites=[
                        {
                            "code": "independently_judged_target_and_baseline",
                            "detail": "Approve and retain an independent target plus declared baseline.",
                        }
                    ],
                ),
            ]
        )

        return {
            "contract_version": CAPABILITY_CONTRACT_VERSION,
            "evaluated_at": evaluated_at,
            "result": result_state(
                "successful",
                "Capability evaluation completed independently of feature results.",
                evaluated_at=evaluated_at,
            ),
            "capabilities": capabilities,
        }

    def get(self, capability_id: str) -> dict[str, Any]:
        catalog = self.query()
        return next(item for item in catalog["capabilities"] if item["id"] == capability_id)
