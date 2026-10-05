from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Callable, Literal
from zoneinfo import ZoneInfo

from disclosures import ConnectionFactory
from events import EventApplication, original_occurrence_ids, publication_interval, select_publication


POLICY_VERSION = "watch-lifecycle@1"
POLICY_TIMEZONE = "America/New_York"
ACTIVE_CALENDAR_DATES = 30
TRIGGERS = {
    "admission",
    "evidence_change",
    "startup_recovery",
    "known_expiry",
    "pre_active_action",
}


def _valid_local_instants(local: datetime, zone: ZoneInfo) -> list[datetime]:
    candidates = []
    for fold in (0, 1):
        aware = local.replace(tzinfo=zone, fold=fold)
        if aware.astimezone(UTC).astimezone(zone).replace(tzinfo=None) == local:
            candidates.append(aware)
    return list({candidate.timestamp(): candidate for candidate in candidates}.values())


def _policy_instant(local: datetime) -> int:
    """Choose the earlier ambiguity or the first valid New York instant after a gap."""
    zone = ZoneInfo(POLICY_TIMEZONE)
    candidates = _valid_local_instants(local, zone)
    if candidates:
        return int(min(candidate.timestamp() for candidate in candidates) * 1000)
    # America/New_York gaps end on a minute boundary. Preserve sub-minute clock
    # semantics for valid times; for a gap, the first valid instant is the boundary.
    candidate = local.replace(second=0, microsecond=0)
    if candidate < local:
        candidate += timedelta(minutes=1)
    for _ in range(181):
        candidates = _valid_local_instants(candidate, zone)
        if candidates:
            return int(min(item.timestamp() for item in candidates) * 1000)
        candidate += timedelta(minutes=1)
    raise ValueError("could not resolve New York lifecycle expiry")


def _add_policy_dates(instant_ms: int) -> int:
    zone = ZoneInfo(POLICY_TIMEZONE)
    local = datetime.fromtimestamp(instant_ms / 1000, zone).replace(tzinfo=None)
    return _policy_instant(local + timedelta(days=ACTIVE_CALENDAR_DATES))


def _expiry_range(start: int, end_exclusive: int) -> tuple[int, int]:
    """Extrema over a supported interval, including clock discontinuities.

    New York's folds/gaps occur on local hour boundaries. Partition both the
    publication clock and the nominal expiry clock there; within each piece the
    calendar-date mapping is increasing or constant. Endpoints alone are unsafe
    when a source-local day ends inside New York's repeated hour.
    """
    zone = ZoneInfo(POLICY_TIMEZONE)
    first = datetime.fromtimestamp(start / 1000, zone).date()
    last = datetime.fromtimestamp((end_exclusive - 1) / 1000, zone).date()
    points = {start, end_exclusive - 1}
    day = first
    while day <= last:
        for hour in range(24):
            local = datetime(day.year, day.month, day.day, hour)
            for instant in _valid_local_instants(local, zone):
                boundary = int(instant.timestamp() * 1000)
                for point in (boundary - 1, boundary):
                    if start <= point < end_exclusive:
                        points.add(point)
        day += timedelta(days=1)
    expiries = [_add_policy_dates(point) for point in points]
    return min(expiries), max(expiries)


def _selected_publication(event: dict) -> tuple[dict | None, dict | None]:
    current = event.get("currentPublication")
    if not current or current.get("status") != "supported" or not current.get("interval"):
        return current, None
    selected = current.get("selectedEvidenceId")
    claim = next((item for item in event["publication"]["evidence"] if item["id"] == selected), None)
    return current, claim


def evaluate_event(event: dict, *, evaluated_at: int, standing_evidence: list[dict] | None = None) -> dict:
    standing = event["standing"]
    withdrawal_pending = False
    withdrawal_observed_at = None
    reinstatement_evidence_id = None
    standing_ids = []
    for fact in standing_evidence or []:
        standing_ids.append(fact["id"])
        if fact["standing"] == "withdrawn":
            if not withdrawal_pending:
                withdrawal_observed_at = fact["observedAt"]
            withdrawal_pending = True
            reinstatement_evidence_id = None
        elif fact["standing"] == "supported" and fact.get("standing_resolution"):
            if withdrawal_observed_at is None or any(
                citation["firstObservedAt"] > withdrawal_observed_at
                for citation in fact["officialCitations"]
            ):
                withdrawal_pending = False
                reinstatement_evidence_id = fact["id"]
        standing = fact["standing"]
    if withdrawal_pending and standing == "supported":
        standing = "withdrawn"
    prerequisite_reasons = event["eligibility"]["watch_admission_prerequisites"]["reasons"]
    standing_reasons = {"evidence_withdrawn", "evidence_unresolved"}
    criteria_reasons = sorted(reason for reason in prerequisite_reasons if reason not in standing_reasons)
    conclusive_failures = set()
    if event["fields"].get("transactionDirection") == "exchange":
        conclusive_failures.add("direction_unresolved_or_out_of_scope")
    if event["fields"].get("assetClass") == "out_of_scope":
        conclusive_failures.add("individual_equity_unresolved_or_out_of_scope")
    unresolved = sorted(reason for reason in criteria_reasons if reason not in conclusive_failures)
    criteria = {"satisfied": not criteria_reasons, "reasons": criteria_reasons,
                "unresolvedReasons": unresolved, "failedReasons": sorted(set(criteria_reasons) & conclusive_failures)}
    if standing == "supported" and unresolved:
        standing = "unresolved"

    current, claim = _selected_publication(event)
    publication_available = bool(current and current.get("interval")
                                 and current["interval"]["endExclusive"] <= evaluated_at)
    expiry_support: dict
    next_evaluation_at = None
    if current and claim and current["interval"]["precision"] == "exact":
        expires_at = _add_policy_dates(current["interval"]["start"])
        expiry_support = {
            "status": "exact",
            "expiresAt": expires_at,
            "policyTimezone": POLICY_TIMEZONE,
            "publicationPrecision": "exact",
            "sourceTimezone": claim.get("timezone"),
        }
        if evaluated_at < expires_at:
            recency = {"status": "within_window"}
            next_evaluation_at = expires_at
        else:
            recency = {"status": "expired"}
    elif current and claim:
        start = current["interval"]["start"]
        end = current["interval"]["endExclusive"]
        earliest, latest = _expiry_range(start, end)
        expiry_support = {
            "status": "interval",
            "earliestExpiryAt": earliest,
            "latestExpiryAt": latest,
            "policyTimezone": POLICY_TIMEZONE,
            "publicationPrecision": current["interval"]["precision"],
            "sourceTimezone": claim.get("timezone"),
        }
        if evaluated_at < earliest:
            recency = {"status": "within_window"}
            next_evaluation_at = earliest
        elif evaluated_at >= latest:
            recency = {"status": "expired"}
        else:
            recency = {"status": "expiry_uncertain"}
            next_evaluation_at = latest
    else:
        reason = "publication_evidence_ambiguous" if current and current.get("status") == "ambiguous" else "publication_age_unknown"
        expiry_support = {"status": "unsupported", "reason": reason, "policyTimezone": POLICY_TIMEZONE}
        recency = {"status": "publication_age_unknown"}

    reasons = list(criteria_reasons)
    if standing == "withdrawn" or withdrawal_pending:
        reasons.append("evidence_withdrawn")
    if standing == "unresolved":
        reasons.append("evidence_unresolved")
    if recency["status"] == "expired":
        reasons.append("expired")
    elif recency["status"] == "expiry_uncertain":
        reasons.append("expiry_uncertain")
    elif recency["status"] == "publication_age_unknown":
        reasons.append("publication_age_unknown")
    if current and current.get("interval") and not publication_available:
        reasons.append("publication_not_available_at_evaluation")
    reasons = sorted(set(reasons))
    active = standing == "supported" and criteria["satisfied"] and recency["status"] == "within_window" and publication_available
    return {
        "policyVersion": POLICY_VERSION,
        "evaluatedAt": evaluated_at,
        "evidenceStanding": {
            "status": standing,
            "evidenceIds": standing_ids,
            "withdrawalPending": withdrawal_pending,
            "reinstatementEvidenceId": reinstatement_evidence_id,
        },
        "admissionCriteria": criteria,
        "recency": recency,
        "expirySupport": expiry_support,
        "activeEligibility": {"eligible": active, "reasons": reasons},
        "lifecycleReasons": reasons,
        "nextEvaluationAt": next_evaluation_at,
        "sourceEvent": {
            "eventId": event["id"],
            "occurrenceIds": event["occurrenceIds"],
        },
        "publicationSupport": {"assessment": current, "selectedEvidence": claim},
        "transactionDate": event["fields"].get("transactionDate"),
    }


def _semantic_state(assessment: dict) -> dict:
    state = {key: assessment[key] for key in (
        "admissionCriteria",
        "recency",
        "expirySupport",
        "activeEligibility",
        "lifecycleReasons",
        "nextEvaluationAt",
    )}
    state["evidenceStanding"] = {key: assessment["evidenceStanding"][key] for key in ("status", "withdrawalPending")}
    return state


def _transition_reasons(previous: dict | None, current: dict) -> list[str]:
    if previous is None:
        return ["admitted"]
    reasons = []
    old_standing = previous["evidenceStanding"]["status"]
    new_standing = current["evidenceStanding"]["status"]
    if previous["evidenceStanding"]["withdrawalPending"] and not current["evidenceStanding"]["withdrawalPending"]:
        reasons.append("reinstated")
    if old_standing != new_standing:
        if old_standing == "withdrawn" and new_standing == "supported":
            reasons.append("reinstated")
        elif new_standing == "withdrawn":
            reasons.append("withdrawn")
        elif new_standing == "unresolved":
            reasons.append("standing_unresolved")
        else:
            reasons.append("standing_supported")
    if previous["admissionCriteria"] != current["admissionCriteria"]:
        reasons.append("admission_criteria_restored" if current["admissionCriteria"]["satisfied"] else "admission_criteria_failed")
    if previous["recency"]["status"] != current["recency"]["status"]:
        names = {
            "expired": "expired",
            "expiry_uncertain": "expiry_uncertain",
            "publication_age_unknown": "publication_age_unknown",
            "within_window": "publication_time_established",
        }
        reasons.append(names[current["recency"]["status"]])
    if previous["expirySupport"] != current["expirySupport"] and not reasons:
        reasons.append("expiry_support_changed")
    return sorted(set(reasons or ["assessment_changed"]))


class WatchApplication:
    """Deterministic Watch Event lifecycle over recorded #28 system observations."""

    def __init__(self, connection_factory: ConnectionFactory, clock: Callable[[], int] | None = None):
        self._connection_factory = connection_factory
        self._clock = clock or (lambda: int(time.time() * 1000))

    @staticmethod
    def _source_snapshot(view: dict, event: dict, conn, original_version: str | None = None) -> dict:
        if original_version is None:
            normalization = event["provenance"]["normalization"]
            row = conn.execute(
                "SELECT r.artifact_version_id FROM disclosure_normalizations n "
                "JOIN disclosure_row_occurrences r ON r.id = n.row_occurrence_id WHERE n.id = ?",
                (normalization["id"],),
            ).fetchone() if normalization else None
            original_version = row["artifact_version_id"] if row else next(
                row["artifactVersionId"] for row in event["provenance"]["rows"] if row["sourceAuthority"] == "official")
        eligible_ids = set(view["inputManifest"]["assertionIds"])
        # #28 already resolves current verified occurrence membership. Its directed
        # amendment contract identifies representations that are not originals;
        # neither those nor unverified/separate occurrences supply a new clock.
        originals = original_occurrence_ids(event["occurrenceIds"], event["provenance"]["relationships"])
        clock_versions = {item["artifactVersionId"] for item in event["provenance"]["rows"]
                          if item["sourceAuthority"] == "official" and item["occurrenceId"] in originals}
        standing_evidence = []
        claims = []
        for row in conn.execute("SELECT rowid AS sequence, * FROM event_evidence_assertions ORDER BY observed_at, rowid"):
            if row["id"] in eligible_ids:
                fact = json.loads(row["assertion_json"])
                if fact.get("occurrence_id") in event["occurrenceIds"] and fact.get("standing"):
                    official_citations = []
                    for citation in fact["citations"]:
                        version = conn.execute(
                            "SELECT v.first_observed_at FROM disclosure_artifact_versions v "
                            "JOIN disclosure_artifacts a ON a.id = v.artifact_id "
                            "WHERE v.id = ? AND a.source_authority = 'official'",
                            (citation["artifact_version_id"],),
                        ).fetchone()
                        if version:
                            official_citations.append({"artifactVersionId": citation["artifact_version_id"],
                                                       "firstObservedAt": version["first_observed_at"]})
                    standing_evidence.append(dict(fact, id=row["id"], observedAt=row["observed_at"],
                                                  officialCitations=official_citations))
                if (fact["kind"] == "publication" and fact["artifact_version_id"] in clock_versions
                        and fact["public_at"] is not None and fact["public_at"] <= view["asOf"]):
                    interval = publication_interval(fact)
                    if interval is not None and interval[1] <= view["asOf"]:
                        claims.append(dict(fact, id=row["id"], observed_at=row["observed_at"], sequence=row["sequence"]))
        # Publication dates of different verified representations can differ.
        # Narrow/check conflicting claims within each artifact using #28, then
        # choose the earliest supported original availability, never a later copy.
        candidates = []
        ambiguous = False
        for version_id in sorted(clock_versions):
            candidate, conflict = select_publication([claim for claim in claims if claim["artifact_version_id"] == version_id])
            ambiguous |= conflict
            if candidate:
                candidates.append(candidate)
        selected = min(candidates, key=lambda claim: (*publication_interval(claim), claim["observed_at"], claim["sequence"]),
                       default=None) if not ambiguous else None
        interval = publication_interval(selected) if selected else None
        proof_observed_at = selected["observed_at"] if selected else None
        if selected and selected["precision"] == "date":
            # First availability is the minimum over the original representations,
            # not an intersection of their different publication dates. Bound its
            # upper end by every copy, retaining an interval at storage precision.
            upper_claim = min(candidates, key=lambda claim: publication_interval(claim)[1]
                              - (1 if claim["precision"] == "date" else 0))
            upper = publication_interval(upper_claim)[1] - (1 if upper_claim["precision"] == "date" else 0)
            interval = interval[0], upper + 1
            proof_observed_at = max(proof_observed_at, upper_claim["observed_at"])
        clock_publication = {
            "status": "ambiguous" if ambiguous else "supported" if selected else "unknown",
            "interval": {"start": interval[0], "endExclusive": interval[1], "precision": selected["precision"]} if interval else None,
            "selectedEvidenceId": selected["id"] if selected else None,
            "proofObservedAt": proof_observed_at,
        }
        original_occurrence = next(item["occurrenceId"] for item in event["provenance"]["rows"]
                                   if item["artifactVersionId"] == original_version)
        conflicting_watches = []
        for watch_row in conn.execute(
            "SELECT * FROM watch_events WHERE admitted_at <= ? AND population = "
            "(SELECT a.population FROM disclosure_artifact_versions v JOIN disclosure_artifacts a "
            "ON a.id = v.artifact_id WHERE v.id = ?)", (view["asOf"], original_version),
        ):
            watch = WatchApplication._watch_row(watch_row)
            if watch["originalOccurrenceId"] != original_occurrence and watch["originalOccurrenceId"] in event["occurrenceIds"]:
                conflicting_watches.append(watch["id"])
        return {
            "methodVersion": view["methodVersion"],
            "computedAt": view["computedAt"],
            "perspective": view["perspective"],
            "asOf": view["asOf"],
            "mode": view["mode"],
            "originalAsOf": view["originalAsOf"],
            "inputManifest": view["inputManifest"],
            "event": event,
            "standingEvidence": standing_evidence,
            "originalArtifactVersionId": original_version,
            "clockPublication": clock_publication,
            "clockPublicationEvidence": claims,
            "conflictingWatchIds": sorted(conflicting_watches),
        }

    @staticmethod
    def _event_for_watch(view: dict, watch: dict) -> dict:
        matches = [event for event in view["events"] if watch["originalOccurrenceId"] in event["occurrenceIds"]]
        if len(matches) != 1:
            raise ValueError("admitted Event is not uniquely represented in the current system-observation view")
        return matches[0]

    @staticmethod
    def _watch_row(row) -> dict:
        source = json.loads(row["admission_event_view_json"])
        original_occurrence = next(item["occurrenceId"] for item in source["event"]["provenance"]["rows"]
                                   if item["artifactVersionId"] == source["originalArtifactVersionId"])
        return {
            "id": row["id"],
            "eventId": row["event_id"],
            "occurrenceIds": json.loads(row["occurrence_ids_json"]),
            "discoveredAt": row["discovered_at"],
            "officialEvidenceFirstObservedAt": row["official_evidence_first_observed_at"],
            "verifiedAt": row["verified_at"],
            "admittedAt": row["admitted_at"],
            "originalArtifactVersionId": source["originalArtifactVersionId"],
            "originalOccurrenceId": original_occurrence,
        }

    @staticmethod
    def _history_row(row) -> dict:
        return {
            "id": row["id"],
            "evaluatedAt": row["evaluated_at"],
            "persistedAt": row["persisted_at"],
            "trigger": row["trigger"],
            "policyVersion": row["policy_version"],
            "transitionReasons": json.loads(row["transition_reasons_json"]),
            "assessment": json.loads(row["assessment_json"]),
            "recordType": "recorded_historical_state",
            "sourceEventView": json.loads(row["source_event_view_json"]),
        }

    @contextmanager
    def _transaction(self, *, write: bool):
        with self._connection_factory() as conn:
            conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            now = self._clock()

            @contextmanager
            def bound_connection():
                # Nested evidence reads share the outer snapshot and never commit.
                yield conn

            yield conn, EventApplication(bound_connection, lambda: now), now

    @staticmethod
    def _derive(events: EventApplication, *, population: str, as_of: int,
                mode: str = "historical_recomputation", original_as_of: int | None = None) -> dict:
        return events.derive(population=population, perspective="system_observation", as_of=as_of,
                             mode=mode, original_as_of=original_as_of)

    def _load_watch(self, conn, watch_event_id: str, *, population: str) -> dict:
        row = conn.execute("SELECT * FROM watch_events WHERE id = ? AND population = ?",
                           (watch_event_id, population)).fetchone()
        if row is None:
            raise KeyError(watch_event_id)
        return self._watch_row(row)

    def _history(self, conn, watch_event_id: str) -> list[dict]:
        rows = conn.execute(
            "SELECT rowid AS sequence, * FROM watch_lifecycle_history WHERE watch_event_id = ? ORDER BY sequence",
            (watch_event_id,),
        ).fetchall()
        return [self._history_row(row) for row in rows]

    @staticmethod
    def _last_assessment(conn, watch_event_id: str) -> tuple[dict | None, object | None]:
        row = conn.execute(
            "SELECT rowid AS sequence, * FROM watch_lifecycle_history WHERE watch_event_id = ? ORDER BY sequence DESC LIMIT 1",
            (watch_event_id,),
        ).fetchone()
        return (json.loads(row["assessment_json"]), row) if row else (None, None)

    def _persist_if_changed(self, conn, *, watch_event_id: str, source: dict, assessment: dict,
                            trigger: str, persisted_at: int) -> bool:
        previous, _ = self._last_assessment(conn, watch_event_id)
        if previous is not None and _semantic_state(previous) == _semantic_state(assessment):
            return False
        conn.execute(
            "INSERT INTO watch_lifecycle_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid.uuid4()), watch_event_id, assessment["evaluatedAt"], persisted_at,
                trigger, POLICY_VERSION, json.dumps(_transition_reasons(previous, assessment)),
                json.dumps(source, sort_keys=True), json.dumps(assessment, sort_keys=True),
            ),
        )
        return True

    def admit(self, event_id: str, *, population: str) -> dict:
        with self._transaction(write=True) as (conn, events, now):
            view = self._derive(events, population=population, as_of=now)
            event = next((item for item in view["events"] if item["id"] == event_id), None)
            if event is None:
                raise KeyError(event_id)
            occurrence_ids = set(event["occurrenceIds"])
            matches = [row for row in conn.execute("SELECT * FROM watch_events WHERE population = ?", (population,))
                       if row["event_id"] == event_id or occurrence_ids & set(json.loads(row["occurrence_ids_json"]))]
            if len(matches) > 1:
                raise ValueError("Event corresponds to multiple existing watches; occurrence verification must be resolved")
            if not matches:
                prerequisites = event["eligibility"]["watch_admission_prerequisites"]
                if not prerequisites["eligible"]:
                    raise ValueError("Event does not satisfy Watch Event admission prerequisites: " + ", ".join(prerequisites["reasons"]))
                source = self._source_snapshot(view, event, conn)
                assessment = self._evaluate(source, now)
                if assessment["evidenceStanding"]["status"] != "supported":
                    raise ValueError("withdrawn evidence requires explicit official reinstatement before admission")
                discovery_times = [event["firstObservedAt"]]
                filing_ids = {(row["sourceFiling"] or {}).get("id") for row in event["provenance"]["rows"]}
                discovery_times.extend(row["discovered_at"] for row in conn.execute(
                    "SELECT id, discovered_at FROM disclosure_source_filings WHERE population = ? AND discovered_at <= ?",
                    (population, now)) if row["id"] in filing_ids)
                watch_id = str(uuid.uuid4())
                conn.execute(
                    "INSERT INTO watch_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        watch_id, population, event_id, json.dumps(sorted(occurrence_ids)),
                        min(discovery_times), event["officialEvidenceFirstObservedAt"],
                        now, now, json.dumps(source, sort_keys=True),
                    ),
                )
            else:
                watch = self._watch_row(matches[0])
                watch_id = watch["id"]
                event = self._event_for_watch(view, watch)
                source = self._source_snapshot(view, event, conn, watch["originalArtifactVersionId"])
                assessment = self._evaluate(source, now)
            self._persist_if_changed(conn, watch_event_id=watch_id, source=source,
                                     assessment=assessment, trigger="admission" if not matches else "evidence_change",
                                     persisted_at=self._clock())
        return self.get(watch_id, population=population)

    @staticmethod
    def _evaluate(source: dict, now: int) -> dict:
        event = source["event"]
        clock_event = dict(event, currentPublication=source["clockPublication"],
                           publication=dict(event["publication"], evidence=source["clockPublicationEvidence"]))
        if source["conflictingWatchIds"]:
            prerequisites = event["eligibility"]["watch_admission_prerequisites"]
            clock_event["eligibility"] = dict(event["eligibility"], watch_admission_prerequisites={
                "eligible": False, "reasons": sorted(set(prerequisites["reasons"]) | {"admitted_occurrence_identity_conflict"})})
        return evaluate_event(clock_event, evaluated_at=now, standing_evidence=source["standingEvidence"])

    def _reevaluate(self, conn, watch: dict, *, trigger: str, now: int, view: dict) -> tuple[bool, dict]:
        if trigger not in TRIGGERS:
            raise ValueError("unsupported Watch Event reevaluation trigger")
        event = self._event_for_watch(view, watch)
        source = self._source_snapshot(view, event, conn, watch["originalArtifactVersionId"])
        assessment = self._evaluate(source, now)
        changed = self._persist_if_changed(conn, watch_event_id=watch["id"], source=source,
                                           assessment=assessment, trigger=trigger, persisted_at=self._clock())
        return changed, assessment

    def reevaluate_all(self, *, population: str, trigger: Literal["evidence_change", "startup_recovery"]) -> int:
        with self._transaction(write=True) as (conn, events, now):
            watches = [self._watch_row(row) for row in conn.execute(
                "SELECT * FROM watch_events WHERE population = ? ORDER BY admitted_at, id", (population,))]
            if not watches:
                return 0
            view = self._derive(events, population=population, as_of=now)
            return sum(self._reevaluate(conn, watch, trigger=trigger, now=now, view=view)[0] for watch in watches)

    def reevaluate_due(self, *, population: str) -> int:
        with self._transaction(write=True) as (conn, events, now):
            watches = [self._watch_row(row) for row in conn.execute(
                "SELECT * FROM watch_events WHERE population = ? ORDER BY admitted_at, id", (population,))]
            due = []
            for watch in watches:
                previous, _ = self._last_assessment(conn, watch["id"])
                if previous and previous.get("nextEvaluationAt") is not None and previous["nextEvaluationAt"] <= now:
                    due.append(watch)
            if not due:
                return 0
            view = self._derive(events, population=population, as_of=now)
            return sum(self._reevaluate(conn, watch, trigger="known_expiry", now=now, view=view)[0] for watch in due)

    def next_evaluation_at(self, *, population: str) -> int | None:
        with self._connection_factory() as conn:
            boundaries = []
            for row in conn.execute("SELECT id FROM watch_events WHERE population = ?", (population,)).fetchall():
                previous, _ = self._last_assessment(conn, row["id"])
                if previous and previous.get("nextEvaluationAt") is not None:
                    boundaries.append(previous["nextEvaluationAt"])
        return min(boundaries, default=None)

    def get(self, watch_event_id: str, *, population: str) -> dict:
        with self._transaction(write=False) as (conn, events, now):
            watch = self._load_watch(conn, watch_event_id, population=population)
            view = self._derive(events, population=population, as_of=now)
            return self._read_model(conn, watch, view=view, now=now)

    def _read_model(self, conn, watch: dict, *, view: dict, now: int) -> dict:
        history = self._history(conn, watch["id"])
        event = self._event_for_watch(view, watch)
        source = self._source_snapshot(view, event, conn, watch["originalArtifactVersionId"])
        current = self._evaluate(source, now)
        last = history[-1]["assessment"]
        return {
            "watchEvent": watch,
            "currentEvaluation": current,
            "lastPersistedAssessment": last,
            "lastPersistedAssessmentIsStale": last["evaluatedAt"] < now,
            "currentDiffersFromLastPersisted": _semantic_state(current) != _semantic_state(last),
            "lifecycleHistory": history,
            "currentEvent": event,
        }

    def list(self, *, population: str) -> dict:
        with self._transaction(write=False) as (conn, events, now):
            watches = [self._watch_row(row) for row in conn.execute(
                "SELECT * FROM watch_events WHERE population = ? ORDER BY admitted_at DESC, id", (population,))]
            view = self._derive(events, population=population, as_of=now) if watches else None
            items = [self._read_model(conn, watch, view=view, now=now) for watch in watches]
            return {"policyVersion": POLICY_VERSION, "evaluatedAt": now, "watchEvents": items,
                    "state": "empty" if not items else "complete"}

    def authorize_active_action(self, watch_event_id: str, *, population: str) -> dict:
        with self._transaction(write=True) as (conn, events, now):
            watch = self._load_watch(conn, watch_event_id, population=population)
            view = self._derive(events, population=population, as_of=now)
            _, current = self._reevaluate(conn, watch, trigger="pre_active_action", now=now, view=view)
            return {"authorized": current["activeEligibility"]["eligible"], "evaluatedAt": now,
                    "policyVersion": POLICY_VERSION, "evaluation": current,
                    "validFor": "immediate_application_action_only"}

    def _assessment_record(self, assessment_id: str, *, population: str) -> tuple[dict, dict, dict]:
        with self._connection_factory() as conn:
            row = conn.execute(
                "SELECT h.*, w.population, w.occurrence_ids_json FROM watch_lifecycle_history h "
                "JOIN watch_events w ON w.id = h.watch_event_id WHERE h.id = ? AND w.population = ?",
                (assessment_id, population),
            ).fetchone()
        if row is None:
            raise KeyError(assessment_id)
        watch = {"id": row["watch_event_id"], "occurrenceIds": json.loads(row["occurrence_ids_json"])}
        return watch, json.loads(row["source_event_view_json"]), json.loads(row["assessment_json"])

    def recorded_assessment(self, watch_event_id: str, assessment_id: str, *, population: str) -> dict:
        with self._connection_factory() as conn:
            row = conn.execute(
                "SELECT h.* FROM watch_lifecycle_history h JOIN watch_events w ON w.id = h.watch_event_id "
                "WHERE h.id = ? AND w.id = ? AND w.population = ?", (assessment_id, watch_event_id, population),
            ).fetchone()
        if row is None:
            raise KeyError(assessment_id)
        return self._history_row(row)

    def reproduce(self, assessment_id: str, *, population: str) -> dict:
        _, source, recorded = self._assessment_record(assessment_id, population=population)
        if recorded["policyVersion"] != POLICY_VERSION:
            raise ValueError("recorded Watch policy version is not available for deterministic reproduction")
        from events import METHOD_VERSION
        if source["methodVersion"] != METHOD_VERSION:
            raise ValueError("recorded Event method version is not available for deterministic reproduction")
        with self._transaction(write=False) as (conn, events, now):
            view = events.derive(population=population, perspective=source["perspective"],
                                 as_of=source["asOf"], mode=source["mode"], original_as_of=source["originalAsOf"],
                                 _manifest=source["inputManifest"])
            event = next((item for item in view["events"] if item["id"] == source["event"]["id"]), None)
            if event != source["event"]:
                raise ValueError("retained Event inputs no longer reproduce the recorded Watch source view")
            reproduced_source = self._source_snapshot(view, event, conn, source["originalArtifactVersionId"])
            if reproduced_source != source:
                raise ValueError("retained evidence no longer reproduces the recorded Watch source view")
            reproduced = self._evaluate(reproduced_source, recorded["evaluatedAt"])
        if reproduced != recorded:
            raise ValueError("retained Watch inputs no longer reproduce the recorded assessment")
        return {"recordType": "deterministic_reproduction", "recordedAssessmentId": assessment_id,
                "reproducedAt": self._clock(), "output": reproduced}

    def historical_recompute(self, assessment_id: str, *, population: str) -> dict:
        watch, _, recorded = self._assessment_record(assessment_id, population=population)
        with self._transaction(write=False) as (conn, events, now):
            watch = self._load_watch(conn, watch["id"], population=population)
            view = self._derive(events, population=population, as_of=recorded["evaluatedAt"])
            event = self._event_for_watch(view, watch)
            source = self._source_snapshot(view, event, conn, watch["originalArtifactVersionId"])
            output = self._evaluate(source, recorded["evaluatedAt"])
        return {"recordType": "historical_recomputation", "recordedAssessmentId": assessment_id,
                "evidenceAsOf": recorded["evaluatedAt"], "computedAt": self._clock(), "output": output}

    def corrected_retrospective(self, assessment_id: str, *, population: str, as_of: int) -> dict:
        watch, _, recorded = self._assessment_record(assessment_id, population=population)
        if as_of <= recorded["evaluatedAt"]:
            raise ValueError("corrected-retrospective evidence boundary must be later than the recorded assessment")
        with self._transaction(write=False) as (conn, events, now):
            watch = self._load_watch(conn, watch["id"], population=population)
            view = self._derive(events, population=population, as_of=as_of, mode="corrected_retrospective",
                                original_as_of=recorded["evaluatedAt"])
            event = self._event_for_watch(view, watch)
            source = self._source_snapshot(view, event, conn, watch["originalArtifactVersionId"])
            output = self._evaluate(source, recorded["evaluatedAt"])
        return {"recordType": "corrected_retrospective", "recordedAssessmentId": assessment_id,
                "originalEvaluationAt": recorded["evaluatedAt"], "evidenceAsOf": as_of,
                "computedAt": self._clock(), "output": output}
