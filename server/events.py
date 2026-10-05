from __future__ import annotations

import json
import time
import uuid
from collections import Counter
from datetime import date, datetime, time as day_time, timedelta
from typing import Any, Callable
from zoneinfo import ZoneInfo

from disclosures import ConnectionFactory, DisclosureApplication
from event_contract import ASSERTION_ADAPTER, ViewCommand


METHOD_VERSION = "event-pit@1"
POPULATIONS = {"real", "test", "demo", "evaluation"}


def publication_interval(claim: dict) -> tuple[int, int] | None:
    """The upper end of a date interval is a conservative boundary, not publication."""
    if claim["precision"] == "exact":
        instant = int(datetime.fromisoformat(claim["raw_value"]).timestamp() * 1000)
        return instant, instant
    if claim["precision"] == "date" and claim["timezone"]:
        local_date = date.fromisoformat(claim["raw_value"])
        zone = ZoneInfo(claim["timezone"])
        start = datetime.combine(local_date, day_time(), zone)
        end = datetime.combine(local_date + timedelta(days=1), day_time(), zone)
        return int(start.timestamp() * 1000), int(end.timestamp() * 1000)
    return None


def resolve_identities(facts: list[dict], scope_date: str | None) -> dict:
    identities = {}
    for identity_type in ("member", "security"):
        mappings = [fact for fact in facts if fact["kind"] == "identity" and fact["identity_type"] == identity_type
                    and scope_date is not None and fact["valid_from"] <= scope_date
                    and (fact["valid_to"] is None or scope_date < fact["valid_to"])]
        keys = {(fact["identity_id"], fact.get("listing_id"), fact.get("calendar_id")) for fact in mappings}
        identities[identity_type] = {"status": "resolved" if len(keys) == 1 else "ambiguous" if keys else "unresolved",
                                    "identity": mappings[0] if len(keys) == 1 else None,
                                    "evidenceIds": sorted(fact["id"] for fact in mappings)}
    return identities


def select_publication(claims: list[dict]) -> tuple[dict | None, bool]:
    """Narrow compatible publication evidence; preserve conflicting claims."""
    exact = [claim for claim in claims if claim["precision"] == "exact"]
    dates = [claim for claim in claims if claim["precision"] == "date"]
    if exact:
        instants = {publication_interval(claim)[0] for claim in exact}
        if len(instants) != 1:
            return None, True
        instant = next(iter(instants))
        if any(not publication_interval(claim)[0] <= instant < publication_interval(claim)[1] for claim in dates):
            return None, True
        return min(exact, key=lambda claim: (claim["public_at"], claim["observed_at"], claim["sequence"])), False
    if dates:
        if len({publication_interval(claim) for claim in dates}) != 1:
            return None, True
        return min(dates, key=lambda claim: (claim["public_at"], claim["observed_at"], claim["sequence"])), False
    return None, False


def session_anchor(facts: list[dict], security: dict | None, boundary: int | None, public_boundary, cutoff: int | None) -> dict | None:
    if security is None or boundary is None or cutoff is None:
        return None
    calendars = [fact for fact in facts if fact["kind"] == "calendar" and fact["calendar_id"] == security["calendar_id"]
                 and public_boundary(fact) is not None and public_boundary(fact) <= cutoff
                 and fact["coverage_start"] <= boundary < fact["coverage_end"]]
    proposals = []
    for calendar in calendars:
        later = [session for session in calendar["sessions"] if session["open_at"] > boundary]
        if later:
            proposals.append((min(later, key=lambda session: session["open_at"]), calendar))
    if proposals and len({(session["open_at"], session["session_date"], calendar["timezone"]) for session, calendar in proposals}) == 1:
        session, calendar = min(proposals, key=lambda proposal: proposal[1]["sequence"])
        return dict(session, calendarId=calendar["calendar_id"], timezone=calendar["timezone"],
                    evidenceId=calendar["id"], strictAfter=True)
    return None


def occurrence_groups(rows: dict, versions: dict, relations: list[dict]) -> tuple[dict, set[str]]:
    parent = {key: key for key in rows}

    def root(key):
        while parent[key] != key:
            key = parent[key]
        return key

    for relation in relations:
        if relation["status"] != "verified":
            continue
        left, right = root(relation["left_occurrence_id"]), root(relation["right_occurrence_id"])
        first, second = sorted((left, right), key=lambda key: (versions[rows[key]["version_id"]]["observed_at"], key))
        parent[second] = first
    tentative = {}
    for key in rows:
        tentative.setdefault(root(key), []).append(key)
    groups, conflicts = {}, set()
    for origin, members in tentative.items():
        if len({rows[key]["version_id"] for key in members}) != len(members):
            # A valid current verification graph does not guarantee a valid graph
            # under a different historical/public ordering. Never choose which of
            # contradictory verified edges is true or collapse same-version rows.
            conflicts.update(members)
            groups.update({key: [key] for key in members})
        else:
            groups[origin] = members
    return groups, conflicts


def original_occurrence_ids(occurrence_ids: list[str], relations: list[dict]) -> set[str]:
    """Original representations under the current verified #28 relationships.

    A same-occurrence copy of an amendment is still an amendment representation,
    not independent evidence of the original occurrence's first publication.
    """
    members = set(occurrence_ids)
    amendments = {relation["right_occurrence_id"] for relation in relations
                  if relation["status"] == "verified" and relation["relation"] == "amendment"
                  and relation["right_occurrence_id"] in members}
    copies = [relation for relation in relations if relation["status"] == "verified"
              and relation["relation"] == "same_occurrence"
              and {relation["left_occurrence_id"], relation["right_occurrence_id"]} <= members]
    while True:
        previous = set(amendments)
        for relation in copies:
            pair = {relation["left_occurrence_id"], relation["right_occurrence_id"]}
            if pair & amendments:
                amendments.update(pair)
        if amendments == previous:
            return members - amendments


def filing_coverage(events: list[dict], versions: dict, rows: dict) -> list[dict]:
    """Explicit counting units and minima, never filing-size eligibility rules."""
    event_for_row = {row_id: event for event in events for row_id in event["occurrenceIds"]}
    groups = {}
    for row in rows.values():
        groups.setdefault(row["version_id"], []).append(row)
    coverage = []
    for version_id, occurrences in sorted(groups.items()):
        event_ids, securities, literal_tickers = set(), set(), set()
        unresolved, in_scope = 0, 0
        ticker_complete = True
        for row in occurrences:
            event = event_for_row[row["id"]]
            event_ids.add(event["id"])
            identity = event["identities"]["security"]["identity"]
            if identity:
                securities.add(identity["identity_id"])
            else:
                unresolved += 1
            if event["fields"].get("assetClass") == "individual_public_equity" and event["fields"].get("transactionDirection") in {"purchase", "sale"}:
                in_scope += 1
            raw = row["rawFields"]
            ticker = raw.get("ticker") if isinstance(raw, dict) else None
            if isinstance(ticker, str) and ticker:
                literal_tickers.add(ticker)
            else:
                ticker_complete = False
        complete = all(row["parseStatus"] == "parsed" for row in occurrences)
        version = versions[version_id]
        # A partial extraction can leave undiscovered rows; its count is a minimum.
        if not any(extraction["status"] == "succeeded" for extraction in version["extractions"]):
            complete = False
        coverage.append({"artifactVersionId": version_id, "sourceFiling": occurrences[0]["sourceFiling"],
            "sourceRole": version["artifact"]["sourceAuthority"], "reportedRowOccurrences": len(occurrences),
            "occurrenceCountMeaning": "retained_minimum" if not complete else "retained_extraction_count",
            "events": len(event_ids), "interpretableEquityOccurrences": in_scope, "resolvedSecurities": len(securities),
            "unresolvedSecurityOccurrences": unresolved, "literalSourceTickerStrings": len(literal_tickers) if ticker_complete else None,
            "literalTickerMinimum": len(literal_tickers), "literalTickerCompleteness": "complete" if ticker_complete else "indeterminate",
            "completeness": "complete" if complete else "partial", "sizeExclusionApplied": False})
    return coverage


class EventApplication:
    """#27 retained evidence → deterministic, immutable/versioned Event read views."""

    def __init__(self, connection_factory: ConnectionFactory, clock: Callable[[], int] | None = None):
        self._connection_factory = connection_factory
        self._disclosures = DisclosureApplication(connection_factory)
        self._clock = clock or (lambda: int(time.time() * 1000))

    def _inputs(self, population: str):
        if population not in POPULATIONS:
            raise ValueError("unknown population")
        retained = self._disclosures.query_evidence(population=population)
        versions, occurrences = {}, {}
        filings = {filing["id"]: filing for filing in retained["sourceFilings"]}
        for artifact in retained["artifacts"]:
            for version in artifact["versions"]:
                observations = [obs for obs in artifact["retrievalObservations"]
                                if obs["artifactVersionId"] == version["id"]
                                and obs["availabilityStatus"] == "available"]
                if not observations:
                    continue
                versions[version["id"]] = dict(version, artifact=artifact,
                    observed_at=min(obs["observedAt"] for obs in observations), observations=observations)
                for row in version["rowOccurrences"]:
                    occurrences[row["id"]] = dict(row, version_id=version["id"],
                        chamber=filings.get((row["sourceFiling"] or {}).get("id"), {}).get("chamber", "unknown"))
        with self._connection_factory() as conn:
            facts = [dict(json.loads(row["assertion_json"]), id=row["id"], observed_at=row["observed_at"], sequence=row["sequence"])
                     for row in conn.execute("SELECT rowid AS sequence, * FROM event_evidence_assertions WHERE population = ? ORDER BY observed_at, rowid", (population,))]
        return versions, occurrences, facts

    def record_assertion(self, assertion: dict, *, population: str) -> dict:
        command = ASSERTION_ADAPTER.validate_python(assertion)
        fact = json.loads(command.model_dump_json())
        if command.kind in {"interpretation", "correction"}:
            fact["fields"] = command.fields.model_dump(mode="json", exclude_unset=True)
        versions, rows, facts = self._inputs(population)
        now = self._clock()
        for citation in fact["citations"]:
            version = versions.get(citation["artifact_version_id"])
            if version is None:
                raise ValueError("citation must reference retained, successfully retrieved evidence in this population")
            if version["observed_at"] > now:
                raise ValueError("future retrieval cannot support an assertion")
        targets = ([fact["left_occurrence_id"], fact["right_occurrence_id"]]
                   if command.kind == "relationship" else [fact["occurrence_id"]] if "occurrence_id" in fact else [])
        if any(target not in rows for target in targets):
            raise ValueError("target occurrence is not retained in this population")
        if any(versions[rows[target]["version_id"]]["observed_at"] > now for target in targets):
            raise ValueError("future occurrence cannot support an assertion")
        if command.kind == "publication" and fact["artifact_version_id"] not in versions:
            raise ValueError("publication must identify a retained artifact version")
        if command.kind == "relationship":
            if targets[0] == targets[1]:
                raise ValueError("relationship requires distinct occurrences")
            if fact["status"] == "verified" and rows[targets[0]]["version_id"] == rows[targets[1]]["version_id"]:
                raise ValueError("distinct rows in the same artifact remain distinct occurrences")
            # A verified cross-source link needs both separately retained representations.
            if fact["status"] == "verified" and not {rows[t]["version_id"] for t in targets}.issubset(
                {citation["artifact_version_id"] for citation in fact["citations"]}
            ):
                raise ValueError("verification must cite both representations")
            if fact["status"] == "verified":
                # Reject transitive many-to-one matching of distinct retained rows.
                connected = set(targets)
                current_pairs = {}
                for item in facts:
                    if item["kind"] == "relationship" and item["observed_at"] <= now:
                        pair = tuple(sorted((item["left_occurrence_id"], item["right_occurrence_id"])))
                        current_pairs[pair] = item
                verified = [item for item in current_pairs.values() if item["status"] == "verified"]
                for _ in range(len(verified) + 1):
                    previous = set(connected)
                    for item in verified:
                        pair = {item["left_occurrence_id"], item["right_occurrence_id"]}
                        if connected & pair:
                            connected.update(pair)
                    if previous == connected:
                        break
                if len({rows[key]["version_id"] for key in connected}) != len(connected):
                    raise ValueError("verified correspondence would collapse distinct occurrences in one artifact")
        if command.kind in {"interpretation", "correction"}:
            if not any(versions[c["artifact_version_id"]]["artifact"]["sourceAuthority"] == "official"
                       for c in fact["citations"]):
                raise ValueError("Event field interpretation/correction requires official evidence")
        fact_id = str(uuid.uuid4())
        fact["method_version"] = METHOD_VERSION
        with self._connection_factory() as conn:
            conn.execute("INSERT INTO event_evidence_assertions VALUES (?, ?, ?, ?, ?)",
                         (fact_id, population, command.kind, now, json.dumps(fact, sort_keys=True)))
        # Source evidence commits first; lifecycle persistence is application-owned.
        # A crash between these commits is recovered at startup, without backdating.
        from watch_events import WatchApplication
        watch_application = WatchApplication(self._connection_factory, self._clock)
        watch_application.reevaluate_all(population=population, trigger="evidence_change")
        if population == "real":
            from jobs.watch_events import schedule_watch_expiry
            schedule_watch_expiry(application=watch_application)
        return dict(fact, id=fact_id, observed_at=now)

    def derive(self, *, population: str, perspective: str, as_of: int,
               mode: str = "historical_recomputation", original_as_of: int | None = None,
               normalization_ids: list[str] | None = None, _manifest: dict | None = None) -> dict:
        request = ViewCommand(perspective=perspective, as_of=as_of, mode=mode,
                              original_as_of=original_as_of, normalization_ids=normalization_ids or [])
        computed_at = _manifest["computedAt"] if _manifest else self._clock()
        if as_of > computed_at:
            raise ValueError("As-Of cannot be in the future")
        versions, rows, facts = self._inputs(population)
        facts = [fact for fact in facts if fact["observed_at"] <= computed_at]
        if _manifest:
            versions = {key: value for key, value in versions.items() if key in _manifest["artifactVersionIds"]}
            rows = {key: value for key, value in rows.items() if key in _manifest["occurrenceIds"]}
            facts = [fact for fact in facts if fact["id"] in _manifest["assertionIds"]]
            for version in versions.values():
                version["extractions"] = [item for item in version["extractions"] if item["id"] in _manifest["extractionIds"]]
                version["observations"] = [item for item in version["observations"] if item["id"] in _manifest["observationIds"]]
            for row in rows.values():
                row["normalizations"] = [item for item in row["normalizations"] if item["id"] in _manifest["normalizationIds"]]
        for fact in facts:
            if not fact.get("method_version"):
                raise ValueError(f"missing assertion method version: {fact['id']}")
            if fact["method_version"] != METHOD_VERSION:
                raise ValueError(f"unsupported assertion method version: {fact['id']} ({fact['method_version']})")
        input_manifest = {"computedAt": computed_at, "artifactVersionIds": sorted(versions), "occurrenceIds": sorted(rows),
            "assertionIds": sorted(fact["id"] for fact in facts),
            "extractionIds": sorted(item["id"] for version in versions.values() for item in version["extractions"]),
            "normalizationIds": sorted(item["id"] for row in rows.values() for item in row["normalizations"]),
            "observationIds": sorted(item["id"] for version in versions.values() for item in version["observations"])}

        # Availability assertions must themselves be eligible. A later statement about
        # earlier publication cannot be smuggled into that earlier evidence boundary.
        claims = [fact for fact in facts if fact["kind"] == "publication"
                  and fact["artifact_version_id"] in versions
                  and fact["public_at"] is not None and fact["public_at"] <= as_of
                  and (perspective == "public_information" or fact["observed_at"] <= as_of)]
        bounds = {key: version["observed_at"] for key, version in versions.items()}
        # Monotonic relaxation from retrieval upper bounds. A self-cited source
        # publication statement can establish its own version's historical bound;
        # other citations must already have an independently supported boundary.
        for _ in range(len(claims) + 1):
            previous = dict(bounds)
            for claim in claims:
                interval = publication_interval(claim)
                if interval is not None:
                    target = claim["artifact_version_id"]
                    supporting_bounds = [bounds[c["artifact_version_id"]] for c in claim["citations"]
                                         if c["artifact_version_id"] != target]
                    supported_bound = max([interval[1], claim["public_at"]] + supporting_bounds)
                    bounds[target] = min(bounds[target], supported_bound)
            if bounds == previous:
                break

        def fact_boundary(fact):
            if perspective == "system_observation":
                return max([fact["observed_at"]] + [versions[c["artifact_version_id"]]["observed_at"] for c in fact["citations"]])
            if fact["public_at"] is None:
                return None
            return max([fact["public_at"]] + [bounds[c["artifact_version_id"]] for c in fact["citations"]])

        def public_boundary(fact):
            if fact["public_at"] is None:
                return None
            return max([fact["public_at"]] + [bounds[c["artifact_version_id"]] for c in fact["citations"]])

        eligible_facts = [fact for fact in facts if (boundary := fact_boundary(fact)) is not None and boundary <= as_of]
        if perspective == "public_information":
            # Only support publication claims with eligible cited evidence, with a
            # self-citation allowed for publication evidenced by the artifact itself.
            claims = [claim for claim in claims if fact_boundary(claim) is not None and fact_boundary(claim) <= as_of]
        visible_rows = {key: row for key, row in rows.items()
                        if (bounds[row["version_id"]] if perspective == "public_information"
                            else versions[row["version_id"]]["observed_at"]) <= as_of
                        and versions[row["version_id"]]["observed_at"] <= computed_at}
        relations = [fact for fact in eligible_facts if fact["kind"] == "relationship"
                     and fact["left_occurrence_id"] in visible_rows and fact["right_occurrence_id"] in visible_rows]
        # Latest eligible resolution per pair; candidates never participate in union.
        by_pair = {}
        for relation in sorted(relations, key=lambda fact: (fact_boundary(fact), fact["observed_at"], fact["sequence"])):
            by_pair[tuple(sorted((relation["left_occurrence_id"], relation["right_occurrence_id"])))] = relation
        def occurrence_order(key):
            row = visible_rows[key]
            return versions[row["version_id"]]["observed_at"], key
        groups, relationship_conflicts = occurrence_groups(visible_rows, versions, list(by_pair.values()))
        requested_normalizations = set(request.normalization_ids)
        available_normalizations = {n["id"]: row_id for row_id, row in visible_rows.items() for n in row["normalizations"]}
        if not requested_normalizations.issubset(available_normalizations):
            raise ValueError("normalization selection includes unavailable/future source evidence")
        if len({available_normalizations[key] for key in requested_normalizations}) != len(requested_normalizations):
            raise ValueError("select at most one normalization per occurrence")
        if any(n["id"] in requested_normalizations and
               n["normalizedAt"] > computed_at
               for row in visible_rows.values() for n in row["normalizations"]):
            raise ValueError("normalization selection contains a future interpretation")

        events = []
        selected_normalizations = set()
        for origin, occurrence_ids in sorted(groups.items()):
            members = [visible_rows[key] for key in sorted(occurrence_ids)]
            official_rows = [row for row in members if versions[row["version_id"]]["artifact"]["sourceAuthority"] == "official"]
            # Amendments identify the original explicitly; later representations cannot
            # replace its source fields even in a recomputation.
            originals = original_occurrence_ids(occurrence_ids, list(by_pair.values()))
            base_rows = [row for row in official_rows if row["id"] in originals] or official_rows or members
            base = min(base_rows, key=lambda row: (bounds[row["version_id"]], occurrence_order(row["id"])))
            event_claims = [claim for claim in claims if claim["artifact_version_id"] == base["version_id"]]
            supported = [claim for claim in event_claims if (supported_interval := publication_interval(claim)) is not None
                         and supported_interval[1] <= as_of and public_boundary(claim) is not None
                         and public_boundary(claim) <= supported_interval[1]]
            publication, publication_ambiguous = select_publication(supported)
            interval = publication_interval(publication) if publication else None
            later_publication, later_ambiguous = select_publication([
                claim for claim in event_claims if (known_interval := publication_interval(claim)) is not None
                and known_interval[1] <= as_of])
            later_interval = publication_interval(later_publication) if later_publication else None
            later_view_allowed = mode == "corrected_retrospective" or perspective == "system_observation"
            intrinsic_boundary = interval[1] if interval else None
            state_cutoff = as_of if mode == "corrected_retrospective" or perspective == "system_observation" else intrinsic_boundary
            state_facts = [fact for fact in eligible_facts if fact.get("occurrence_id") in occurrence_ids
                           and state_cutoff is not None and fact_boundary(fact) <= state_cutoff]
            state_facts.sort(key=lambda fact: (fact_boundary(fact), fact["observed_at"], fact["sequence"]))
            fields, normalization = {}, None
            base_selections = {n["id"] for n in base["normalizations"]} & requested_normalizations
            norms = [n for n in base["normalizations"] if n["normalizedAt"] <= computed_at
                     and (not base_selections or n["id"] in base_selections)]
            if norms:
                normalization = max(norms, key=lambda n: (n["normalizedAt"], n["methodVersion"], n["id"]))
                selected_normalizations.add(normalization["id"])
                fields = dict(normalization["normalizedFields"])
            intrinsic_fields = dict(fields)
            intrinsic_facts = [fact for fact in eligible_facts if fact.get("occurrence_id") in occurrence_ids
                               and intrinsic_boundary is not None and (boundary := public_boundary(fact)) is not None
                               and boundary <= intrinsic_boundary]
            intrinsic_facts.sort(key=lambda fact: (public_boundary(fact), fact["observed_at"], fact["sequence"]))
            for fact in intrinsic_facts:
                if fact["kind"] in {"interpretation", "correction"}:
                    intrinsic_fields.update(fact["fields"])
            standing = "supported"
            used_facts = []
            for fact in state_facts:
                if fact["kind"] in {"interpretation", "correction"}:
                    fields.update(fact["fields"])
                    if fact.get("standing"):
                        standing = fact["standing"]
                    used_facts.append(fact["id"])
            # Normalize command keys only in the read model, without touching source values.
            for values in (fields, intrinsic_fields):
                for key in ("transaction_direction", "asset_class", "transaction_date", "amount_lower", "amount_upper"):
                    if key in values:
                        camel = key.split("_")[0] + "".join(part.title() for part in key.split("_")[1:])
                        values[camel] = values.pop(key)
            publication_date = (publication["raw_value"] if publication and publication["precision"] == "date"
                                else datetime.fromisoformat(publication["raw_value"]).date().isoformat() if publication else None)
            current_publication_date = (later_publication["raw_value"] if later_publication and later_publication["precision"] == "date"
                                        else datetime.fromisoformat(later_publication["raw_value"]).date().isoformat() if later_publication else None)
            scope_date = fields.get("transactionDate") or publication_date or (current_publication_date if later_view_allowed else None)
            identities = resolve_identities(state_facts, scope_date)
            intrinsic_identities = resolve_identities(intrinsic_facts, intrinsic_fields.get("transactionDate") or publication_date)
            used_facts.extend(evidence_id for identity in identities.values() for evidence_id in identity["evidenceIds"])
            # A correction may change the retrospective instrument interpretation,
            # but cannot replace an already supported original listing/calendar.
            security = intrinsic_identities["security"]["identity"]
            anchor = session_anchor(eligible_facts, security, intrinsic_boundary, public_boundary, intrinsic_boundary)
            if anchor:
                used_facts.append(anchor["evidenceId"])
            current_publication = {"status": "ambiguous" if later_ambiguous else "supported" if later_publication else "unknown",
                "interval": {"start": later_interval[0], "endExclusive": later_interval[1], "precision": later_publication["precision"]} if later_interval else None,
                "availabilityBoundary": later_interval[1] if later_interval else None,
                "proofAvailableAt": public_boundary(later_publication) if later_publication else None,
                "proofObservedAt": later_publication["observed_at"] if later_publication else None,
                "selectedEvidenceId": later_publication["id"] if later_publication else None,
                "perspective": perspective, "asOf": as_of, "changesOriginalAnchor": False} if later_view_allowed else None
            retrospective_anchor = (session_anchor(eligible_facts, identities["security"]["identity"], later_interval[1], public_boundary, as_of)
                                    if mode == "corrected_retrospective" and later_interval else None)
            primary_pairs = {}
            for relation in sorted(relations, key=lambda fact: (public_boundary(fact) or as_of, fact["sequence"])):
                if intrinsic_boundary is not None and public_boundary(relation) is not None and public_boundary(relation) <= intrinsic_boundary:
                    primary_pairs[tuple(sorted((relation["left_occurrence_id"], relation["right_occurrence_id"])))] = relation
            current_ambiguous_count = any(relation["status"] == "candidate" and relation["counting_ambiguous"]
                                  and ({relation["left_occurrence_id"], relation["right_occurrence_id"]} & set(occurrence_ids))
                                  for relation in by_pair.values())
            primary_ambiguous_count = any(relation["status"] == "candidate" and relation["counting_ambiguous"]
                                   and ({relation["left_occurrence_id"], relation["right_occurrence_id"]} & set(occurrence_ids))
                                   for relation in primary_pairs.values())
            _, intrinsic_relationship_conflicts = occurrence_groups(visible_rows, versions, list(primary_pairs.values()))
            common = []
            if not official_rows:
                common.append("official_evidence_missing")
            if fields.get("transactionDirection") not in {"purchase", "sale"}:
                common.append("direction_unresolved_or_out_of_scope")
            if fields.get("assetClass") != "individual_public_equity":
                common.append("individual_equity_unresolved_or_out_of_scope")
            for identity_type in identities:
                if identities[identity_type]["status"] != "resolved":
                    common.append(f"{identity_type}_identity_{identities[identity_type]['status']}")
            if current_ambiguous_count and (mode == "corrected_retrospective" or perspective == "system_observation"):
                common.append("occurrence_counting_ambiguous")
            if relationship_conflicts & set(occurrence_ids) and (mode == "corrected_retrospective" or perspective == "system_observation"):
                common.append("occurrence_verification_conflict")
            if standing != "supported":
                common.append(f"evidence_{standing}")
            primary = list(common)
            if primary_ambiguous_count:
                primary.append("occurrence_counting_ambiguous")
            if intrinsic_relationship_conflicts & set(occurrence_ids):
                primary.append("occurrence_verification_conflict")
            if interval is None:
                primary.append("publication_availability_unsupported")
            if publication_ambiguous:
                primary.append("publication_availability_ambiguous")
            if any(claim["precision"] == "unknown_timezone" or claim["precision"] == "date" and not claim["timezone"] for claim in event_claims):
                if not interval:
                    primary.append("publication_timezone_unknown")
            if anchor is None:
                primary.append("session_anchor_unavailable")
            if perspective != "public_information":
                primary.append("primary_requires_public_information")
            if mode == "corrected_retrospective":
                primary.append("corrected_retrospective_not_primary")
            if intrinsic_boundary is not None and any(
                relation["status"] == "verified" and public_boundary(relation) is not None
                and relation["relation"] != "amendment"
                and public_boundary(relation) > intrinsic_boundary
                and {relation["left_occurrence_id"], relation["right_occurrence_id"]} & set(occurrence_ids)
                for relation in by_pair.values()
            ):
                primary.append("occurrence_relationship_after_intrinsic_boundary")
            # This is a disclosure prerequisite assessment, never actual admission.
            watch = list(common)
            if perspective != "system_observation":
                watch.append("watch_requires_system_observation")
            contexts = [fact for fact in eligible_facts if fact["kind"] == "context"
                        and fact["occurrence_id"] in occurrence_ids and anchor is not None
                        and fact_boundary(fact) < anchor["open_at"]]
            amount_reasons = []
            if fields.get("amountLower") is None or fields.get("amountUpper") is None:
                amount_reasons.append("amount_unresolved")
            elif fields["amountLower"] > fields["amountUpper"]:
                amount_reasons.append("amount_range_conflict")
            events.append({"id": f"event:{origin}", "occurrenceIds": sorted(occurrence_ids),
                "status": "event" if official_rows else "unverified_discovery_candidate",
                "occurrenceRelationshipStatus": "conflicting_verification" if relationship_conflicts & set(occurrence_ids) else "established",
                "chamber": base["chamber"], "fields": fields, "standing": standing,
                "identities": identities, "publication": {"evidence": event_claims, "selectedEvidenceId": publication["id"] if publication else None,
                    "interval": {"start": interval[0], "endExclusive": interval[1], "precision": publication["precision"]} if interval else None,
                    "availabilityBoundary": intrinsic_boundary, "isExact": bool(publication and publication["precision"] == "exact")},
                "firstObservedAt": min(versions[row["version_id"]]["observed_at"] for row in members),
                "retrievalAvailability": [{"artifactVersionId": row["version_id"],
                    "noLaterThan": versions[row["version_id"]]["observed_at"], "claim": "available_no_later_than_retrieval"} for row in members],
                "officialEvidenceFirstObservedAt": min((versions[row["version_id"]]["observed_at"] for row in official_rows), default=None),
                "anchor": anchor, "intrinsicBoundary": intrinsic_boundary,
                "currentPublication": current_publication, "retrospectiveAnchor": retrospective_anchor,
                "intrinsicState": {"fields": intrinsic_fields, "boundary": intrinsic_boundary,
                    "status": "frozen" if intrinsic_boundary is not None else "publication_boundary_unsupported",
                    "identities": intrinsic_identities,
                    "assertionIds": sorted(fact["id"] for fact in intrinsic_facts), "methodVersion": METHOD_VERSION},
                "stateBoundary": state_cutoff, "preSessionContext": contexts,
                "provenance": {"rows": [{"occurrenceId": row["id"], "artifactVersionId": row["version_id"],
                    "artifactId": versions[row["version_id"]]["artifact"]["id"], "sourceFiling": row["sourceFiling"],
                    "sourceAuthority": versions[row["version_id"]]["artifact"]["sourceAuthority"],
                    "sourceUrl": versions[row["version_id"]]["artifact"]["sourceUrl"],
                    "ordinal": row["ordinal"], "rawFields": row["rawFields"],
                    "retrievalObservationIds": [obs["id"] for obs in versions[row["version_id"]]["observations"]
                        if obs["observedAt"] <= as_of]} for row in members],
                    "normalization": normalization, "assertionIds": sorted(set(used_facts)),
                    "extraction": next((extraction for extraction in versions[base["version_id"]]["extractions"]
                        if normalization and extraction["id"] == normalization["extractionId"]), None),
                    "relationships": [relation for relation in by_pair.values()
                        if {relation["left_occurrence_id"], relation["right_occurrence_id"]} & set(occurrence_ids)]},
                "eligibility": {"retention": {"eligible": True, "reasons": []},
                    "primary_analysis": {"eligible": not primary, "reasons": sorted(set(primary))},
                    "watch_admission_prerequisites": {"eligible": not watch, "reasons": sorted(set(watch))},
                    "latency": {"eligible": bool(fields.get("transactionDate") and interval),
                        "reasons": ([] if fields.get("transactionDate") else ["transaction_date_missing"]) + ([] if interval else ["publication_availability_unsupported"])},
                    "amount_features": {"eligible": not amount_reasons, "reasons": amount_reasons}}})

        if requested_normalizations - selected_normalizations:
            raise ValueError("normalization selection must belong to the original Event representation")
        manifest_versions = {key: version for key, version in versions.items()
                             if (bounds[key] if perspective == "public_information" else version["observed_at"]) <= as_of}
        input_manifest.update(artifactVersionIds=sorted(manifest_versions), occurrenceIds=sorted(visible_rows),
            assertionIds=sorted(fact["id"] for fact in eligible_facts),
            extractionIds=sorted(item["id"] for version in manifest_versions.values() for item in version["extractions"] if item["extractedAt"] <= computed_at),
            normalizationIds=sorted(item["id"] for row in visible_rows.values() for item in row["normalizations"] if item["normalizedAt"] <= computed_at),
            observationIds=sorted(item["id"] for version in manifest_versions.values() for item in version["observations"] if item["observedAt"] <= computed_at))
        reason_counts = Counter(reason for event in events for reason in event["eligibility"]["primary_analysis"]["reasons"])
        readiness = self._disclosures.query_chamber_readiness(population=population)
        for chamber in readiness.values():
            if isinstance(chamber, dict):
                chamber["evaluatedAt"] = computed_at
        return {"methodVersion": METHOD_VERSION, "computedAt": computed_at, "perspective": perspective,
                "asOf": as_of, "mode": mode, "originalAsOf": original_as_of,
                "inputManifest": input_manifest,
                "state": "empty" if not events else "partial" if reason_counts else "complete",
                "events": events, "coverage": {"retainedOccurrences": len(visible_rows), "asOfOccurrences": len(visible_rows),
                    "events": len(events), "officialEvents": sum(event["status"] == "event" for event in events),
                    "primaryDisclosureEligible": sum(event["eligibility"]["primary_analysis"]["eligible"] for event in events),
                    "reasonCounts": dict(sorted(reason_counts.items())), "reasonsNonExclusive": True,
                    "chambers": dict(Counter(event["chamber"] for event in events)),
                    "directions": dict(Counter(event["fields"].get("transactionDirection", "unknown") for event in events)),
                    "calendarYears": dict(Counter(event["anchor"]["session_date"][:4] if event["anchor"] else
                        next((claim["raw_value"][:4] for claim in event["publication"]["evidence"]
                              if claim["id"] == event["publication"]["selectedEvidenceId"]), "unknown") for event in events)),
                    "calendarYearBasis": "anchor_session_or_supported_source_local_publication",
                    "sourceRoles": dict(Counter("official" if event["status"] == "event" else "supporting" for event in events)),
                    "filings": filing_coverage(events, versions, visible_rows),
                    "panelComplete": False, "readiness": readiness},
                "selectedNormalizationIds": sorted(selected_normalizations),
                "marketOutcomes": {"availability": "unavailable", "reasons": ["market_data_contract_not_satisfied"]}}

    def record_view(self, *, population: str, **request: Any) -> dict:
        view = self.derive(population=population, **request)
        view_id = str(uuid.uuid4())
        view = dict(view, id=view_id, recordType="recorded_output")
        with self._connection_factory() as conn:
            conn.execute("INSERT INTO event_recorded_views VALUES (?, ?, ?, ?)",
                         (view_id, population, view["computedAt"], json.dumps(view, sort_keys=True)))
        return view

    def get_recorded_view(self, view_id: str, *, population: str) -> dict:
        with self._connection_factory() as conn:
            row = conn.execute("SELECT view_json FROM event_recorded_views WHERE id = ? AND population = ?", (view_id, population)).fetchone()
        if row is None:
            raise KeyError(view_id)
        return json.loads(row["view_json"])

    def reproduce_recorded_view(self, view_id: str, *, population: str) -> dict:
        recorded = self.get_recorded_view(view_id, population=population)
        if recorded["methodVersion"] != METHOD_VERSION:
            raise ValueError("recorded method version is not available for deterministic reproduction")
        reproduced = self.derive(population=population, perspective=recorded["perspective"], as_of=recorded["asOf"],
            mode=recorded["mode"], original_as_of=recorded["originalAsOf"],
            normalization_ids=recorded["selectedNormalizationIds"], _manifest=recorded["inputManifest"])
        reproduced = dict(reproduced, id=view_id, recordType="recorded_output")
        if reproduced != recorded:
            raise ValueError("retained inputs no longer reproduce the recorded output")
        return {"recordType": "deterministic_reproduction", "recordedViewId": view_id,
                "reproducedAt": self._clock(), "output": reproduced}
