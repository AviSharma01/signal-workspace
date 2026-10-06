import json
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from disclosures import DisclosureApplication, RetrievedArtifact
from events import EventApplication
from tests.ptr_pdf_fixture import ptr_pdf


def ms(value):
    return int(datetime.fromisoformat(value).timestamp() * 1000)


class EventApplicationTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.population = "test"
        self.path = Path(self.directory.name) / "events.db"
        with self.connection() as conn:
            conn.executescript((Path(__file__).parents[1] / "db/schema.sql").read_text())
        self.disclosures = DisclosureApplication(self.connection)
        self.now = ms("2025-07-08T20:00:00-04:00")
        self.events = EventApplication(self.connection, lambda: self.now)

    def tearDown(self):
        self.directory.cleanup()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def test_identical_supporting_occurrences_remain_distinct_candidates(self):
        self.disclosures.ingest_supporting_retrieval(RetrievedArtifact(
            population="test", source_name="kadoa", source_url="https://fixture.example/rows",
            media_type="application/json", content=json.dumps([{"ticker": "ABC"}] * 2).encode(),
            retrieved_at_ms=1000, purpose="manual", freshness_status="unknown", coverage_status="unknown",
        ))
        view = self.events.derive(population="test", perspective="system_observation", as_of=2000)
        self.assertEqual(len(view["events"]), 2)
        self.assertEqual(len({event["id"] for event in view["events"]}), 2)
        for event in view["events"]:
            self.assertEqual(event["status"], "unverified_discovery_candidate")
            self.assertIn("official_evidence_missing", event["eligibility"]["primary_analysis"]["reasons"])
            self.assertFalse(event["eligibility"]["watch_admission_prerequisites"]["eligible"])

    def test_recorded_event_pit_v1_envelope_remains_reproducible(self):
        recorded = self.events.record_view(
            population="test",
            perspective="public_information",
            as_of=self.now,
        )

        self.assertEqual(
            recorded["marketOutcomes"],
            {
                "availability": "unavailable",
                "reasons": ["market_data_contract_not_satisfied"],
            },
        )
        self.assertEqual(
            set(recorded["coverage"]["readiness"]["house"]),
            {
                "chamber",
                "availability",
                "reasonCode",
                "detail",
                "evaluatedAt",
                "governingVersion",
                "unmetPrerequisites",
            },
        )
        self.assertEqual(
            self.events.reproduce_recorded_view(recorded["id"], population="test")["output"],
            recorded,
        )

    def official(self, publication="2025-07-03T09:00:00-04:00", *, document="20030001", count=1,
                 transaction_date="07/01/2025", amount="$1,001 - $15,000", observed=None,
                 asset="Example Corp (ABC) [ST]"):
        observed = observed or ms("2025-07-03T12:00:00-04:00")
        with patch("disclosures.time.time", return_value=observed / 1000):
            result = self.disclosures.ingest_house_filing(RetrievedArtifact(
                population=self.population, source_name="house-clerk",
                source_url=f"https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/{document}.pdf",
                media_type="application/pdf", content=ptr_pdf([
                    ["1", "SP", asset, "P", transaction_date, "07/02/2025", amount, ""]
                ] * count), retrieved_at_ms=observed, purpose="manual", freshness_status="unknown", coverage_status="unknown",
            ), report_year=2025, document_id=document)
        retained = self.disclosures.query_evidence(population=self.population)
        version = next(version for artifact in retained["artifacts"] for version in artifact["versions"]
                       if version["id"] == result["artifactVersionId"])
        rows = version["rowOccurrences"]
        if publication is not None:
            self.assertion("publication", version["id"], ms(publication), artifact_version_id=version["id"],
                           precision="exact", raw_value=publication)
        return version["id"], rows

    def assertion(self, kind, version, public_at, **values):
        citations = values.pop("citations", [{"artifact_version_id": version, "locator": "fixture: explicit cited statement"}])
        return self.events.record_assertion(dict(kind=kind, citations=citations, public_at=public_at,
                                                 basis="retained deterministic fixture evidence", **values), population=self.population)

    def identities(self, version, row, public_at, *, security="security:ABC", valid_from="2020-01-01", valid_to=None):
        self.assertion("identity", version, public_at, occurrence_id=row, identity_type="member",
                       identity_id="member:001", evidence_type="stable_source_identifier",
                       valid_from="2020-01-01", valid_to=None)
        self.assertion("identity", version, public_at, occurrence_id=row, identity_type="security",
                       identity_id=security, evidence_type="historical_listing", valid_from=valid_from,
                       valid_to=valid_to, listing_id=f"listing:{security}", calendar_id="XNYS")
        self.assertion("interpretation", version, public_at, occurrence_id=row,
                       fields={"asset_class": "individual_public_equity"})

    def calendar(self, version, public_at):
        return self.assertion("calendar", version, public_at, calendar_id="XNYS", timezone="America/New_York",
            coverage_start=ms("2025-07-01T00:00:00-04:00"), coverage_end=ms("2025-07-09T00:00:00-04:00"),
            validation="validated_complete_regular_sessions", sessions=[
                {"session_date": day, "open_at": ms(f"{day}T09:30:00-04:00"),
                 "close_at": ms(f"{day}T{close}-04:00")}
                for day, close in [("2025-07-01", "16:00:00"), ("2025-07-02", "16:00:00"),
                                   ("2025-07-03", "13:00:00"), ("2025-07-07", "16:00:00"), ("2025-07-08", "16:00:00")]])

    def view(self, as_of="2025-07-08T20:00:00-04:00", perspective="public_information", **options):
        return self.events.derive(population=self.population, perspective=perspective, as_of=ms(as_of), **options)

    def test_official_rows_have_lossless_provenance_and_eligibility_without_amount_or_transaction_date(self):
        publication = "2025-07-03T09:00:00-04:00"
        version, rows = self.official(publication, count=2, transaction_date="", amount="")
        for row in rows:
            self.identities(version, row["id"], ms(publication))
        self.calendar(version, ms(publication))
        view = self.view()
        self.assertEqual(view["coverage"]["events"], 2)
        for event in view["events"]:
            self.assertTrue(event["eligibility"]["primary_analysis"]["eligible"], event)
            self.assertEqual(event["anchor"]["open_at"], ms("2025-07-03T09:30:00-04:00"))
            self.assertFalse(event["eligibility"]["amount_features"]["eligible"])
            self.assertFalse(event["eligibility"]["latency"]["eligible"])
            self.assertEqual(event["provenance"]["rows"][0]["artifactVersionId"], version)
            self.assertIn("sourcePosition", event["provenance"]["rows"][0]["rawFields"])
            self.assertIsNotNone(event["provenance"]["normalization"]["extractionId"])

    def test_candidate_relationship_never_merges_but_verified_relationship_links_one_event(self):
        publication = ms("2025-07-03T09:00:00-04:00")
        version, rows = self.official()
        self.disclosures.ingest_supporting_retrieval(RetrievedArtifact(
            population="test", source_name="kadoa", source_url="https://fixture.example/rows",
            media_type="application/json", content=b'[{"ticker":"ABC"}]',
            retrieved_at_ms=publication, purpose="manual", freshness_status="unknown", coverage_status="unknown",
        ))
        retained = self.disclosures.query_evidence(population="test")
        supporting = next(artifact["versions"][0] for artifact in retained["artifacts"] if artifact["sourceAuthority"] == "supporting")
        right = supporting["rowOccurrences"][0]["id"]
        citations = [{"artifact_version_id": value, "locator": "verified row correspondence"} for value in [version, supporting["id"]]]
        args = dict(left_occurrence_id=rows[0]["id"], right_occurrence_id=right, citations=citations)
        self.assertion("relationship", version, publication, status="candidate", **args)
        candidate = self.view(perspective="system_observation")
        self.assertEqual(len(candidate["events"]), 2)
        self.assertTrue(all("occurrence_counting_ambiguous" in event["eligibility"]["primary_analysis"]["reasons"] for event in candidate["events"]))
        self.assertion("relationship", version, publication, status="verified", **args)
        verified = self.view()
        self.assertEqual(len(verified["events"]), 1)
        self.assertEqual(len(verified["events"][0]["occurrenceIds"]), 2)
        self.assertEqual({row["sourceAuthority"] for row in verified["events"][0]["provenance"]["rows"]}, {"official", "supporting"})

    def test_publication_strict_after_calendar_anchors(self):
        cases = [
            ("2025-07-03T09:00:00-04:00", "2025-07-03T09:30:00-04:00"),
            ("2025-07-03T09:30:00-04:00", "2025-07-07T09:30:00-04:00"),
            ("2025-07-03T11:00:00-04:00", "2025-07-07T09:30:00-04:00"),
            ("2025-07-03T14:00:00-04:00", "2025-07-07T09:30:00-04:00"),
            ("2025-07-04T09:00:00-04:00", "2025-07-07T09:30:00-04:00"),
            ("2025-07-05T09:00:00-04:00", "2025-07-07T09:30:00-04:00"),
        ]
        for index, (publication, expected) in enumerate(cases):
            with self.subTest(publication=publication):
                version, rows = self.official(publication, document=str(20030100 + index))
                self.identities(version, rows[0]["id"], ms(publication))
                self.calendar(version, ms(publication))
                event = next(event for event in self.view()["events"] if rows[0]["id"] in event["occurrenceIds"])
                self.assertEqual(event["anchor"]["open_at"], ms(expected))

    def test_date_only_publication_is_an_interval_eligible_after_the_source_local_day(self):
        version, rows = self.official(None)
        end = ms("2025-07-04T00:00:00-04:00")
        self.assertion("publication", version, end, artifact_version_id=version,
                       precision="date", raw_value="2025-07-03", timezone="America/New_York")
        self.identities(version, rows[0]["id"], end)
        self.calendar(version, end)
        before_end = self.view("2025-07-03T23:59:59-04:00")["events"][0]
        self.assertFalse(before_end["eligibility"]["primary_analysis"]["eligible"])
        self.assertIsNone(before_end["anchor"])
        event = self.view()["events"][0]
        self.assertEqual(event["publication"]["interval"], {
            "start": ms("2025-07-03T00:00:00-04:00"), "endExclusive": end, "precision": "date"})
        self.assertFalse(event["publication"]["isExact"])
        self.assertEqual(event["anchor"]["open_at"], ms("2025-07-07T09:30:00-04:00"))

    def test_unknown_timezone_and_filing_date_do_not_prove_publication(self):
        for index, (precision, value, timezone) in enumerate([
            ("date", "2025-07-03", None), ("unknown_timezone", "2025-07-03 09:00", None),
            ("filing_date", "2025-07-03", "America/New_York"),
        ]):
            with self.subTest(precision=precision):
                version, _ = self.official(None, document=str(20030300 + index))
                self.assertion("publication", version, ms("2025-07-03T12:00:00-04:00"),
                               artifact_version_id=version, precision=precision, raw_value=value, timezone=timezone)
                event = next(event for event in self.view()["events"] if event["provenance"]["rows"][0]["artifactVersionId"] == version)
                self.assertIsNone(event["anchor"])
                self.assertIsNone(event["publication"]["interval"])
                self.assertIn("publication_availability_unsupported", event["eligibility"]["primary_analysis"]["reasons"])

    def test_delayed_ingestion_keeps_public_and_system_perspectives_separate(self):
        publication = ms("2025-07-03T09:00:00-04:00")
        ingestion = ms("2025-07-07T12:00:00-04:00")
        version, rows = self.official(observed=ingestion)
        self.identities(version, rows[0]["id"], publication)
        self.calendar(version, publication)
        public = self.view("2025-07-03T10:00:00-04:00")["events"][0]
        self.assertTrue(public["eligibility"]["primary_analysis"]["eligible"])
        self.assertEqual(public["firstObservedAt"], ingestion)
        self.assertEqual(self.view("2025-07-03T10:00:00-04:00", "system_observation")["events"], [])
        self.assertEqual(self.view("2025-07-07T13:00:00-04:00", "system_observation")["events"][0]["identities"]["security"]["status"], "unresolved")

    def test_later_mapping_cannot_repair_primary_intrinsic_state(self):
        version, rows = self.official()
        late = ms("2025-07-07T09:00:00-04:00")
        self.identities(version, rows[0]["id"], late)
        self.calendar(version, late)
        historical = self.view()["events"][0]
        self.assertEqual(historical["identities"]["security"]["status"], "unresolved")
        corrected = self.view(mode="corrected_retrospective", original_as_of=ms("2025-07-03T10:00:00-04:00"))["events"][0]
        self.assertEqual(corrected["identities"]["security"]["status"], "resolved")
        self.assertFalse(corrected["eligibility"]["primary_analysis"]["eligible"])
        self.assertIn("corrected_retrospective_not_primary", corrected["eligibility"]["primary_analysis"]["reasons"])

    def test_ticker_reuse_is_historically_scoped_and_ambiguity_is_retained(self):
        version, rows = self.official(transaction_date="07/01/2025")
        public_at = ms("2025-07-03T09:00:00-04:00")
        self.identities(version, rows[0]["id"], public_at, security="old-issuer", valid_to="2025-07-02")
        self.assertion("identity", version, public_at, occurrence_id=rows[0]["id"], identity_type="security",
                       identity_id="new-issuer", evidence_type="historical_listing", valid_from="2025-07-02",
                       listing_id="listing:new", calendar_id="XNYS")
        event = self.view()["events"][0]
        self.assertEqual(event["identities"]["security"]["identity"]["identity_id"], "old-issuer")
        self.assertion("identity", version, public_at, occurrence_id=rows[0]["id"], identity_type="security",
                       identity_id="other-share-class", evidence_type="historical_listing", valid_from="2020-01-01",
                       listing_id="listing:other", calendar_id="XNYS")
        event = self.view()["events"][0]
        self.assertEqual(event["identities"]["security"]["status"], "ambiguous")
        self.assertIn("security_identity_ambiguous", event["eligibility"]["primary_analysis"]["reasons"])
        with self.assertRaises(ValueError):
            self.assertion("identity", version, public_at, occurrence_id=rows[0]["id"], identity_type="security",
                           identity_id="guessed", evidence_type="ticker_equality", valid_from="2020-01-01",
                           listing_id="listing:guess", calendar_id="XNYS")

    def test_scoped_late_correction_preserves_historical_outputs_and_original_anchor(self):
        publication = ms("2025-07-03T09:00:00-04:00")
        version, rows = self.official(count=2)
        for row in rows:
            self.identities(version, row["id"], publication)
        self.calendar(version, publication)
        recorded = self.events.record_view(population="test", perspective="public_information",
                                           as_of=ms("2025-07-03T10:00:00-04:00"))
        self.assertion("correction", version, ms("2025-07-07T10:00:00-04:00"),
                       occurrence_id=rows[0]["id"], fields={"transaction_direction": "sale"})
        historical = self.view()
        self.assertEqual({event["fields"]["transactionDirection"] for event in historical["events"]}, {"purchase"})
        corrected = self.view(mode="corrected_retrospective", original_as_of=recorded["asOf"])
        changed = next(event for event in corrected["events"] if rows[0]["id"] in event["occurrenceIds"])
        untouched = next(event for event in corrected["events"] if rows[1]["id"] in event["occurrenceIds"])
        self.assertEqual(changed["fields"]["transactionDirection"], "sale")
        self.assertEqual(untouched["fields"]["transactionDirection"], "purchase")
        self.assertEqual(changed["anchor"]["open_at"], ms("2025-07-03T09:30:00-04:00"))
        self.assertEqual(self.events.get_recorded_view(recorded["id"], population="test"), recorded)
        self.assertEqual(self.events.reproduce_recorded_view(recorded["id"], population="test")["output"], recorded)

    def test_context_requires_evidence_strictly_before_open(self):
        publication = ms("2025-07-03T09:00:00-04:00")
        version, rows = self.official()
        self.identities(version, rows[0]["id"], publication)
        self.calendar(version, publication)
        for instant, label in [("2025-07-03T09:29:59-04:00", "before"),
                               ("2025-07-03T09:30:00-04:00", "at"), ("2025-07-03T09:31:00-04:00", "after")]:
            self.assertion("context", version, ms(instant), occurrence_id=rows[0]["id"], label=label)
        event = self.view()["events"][0]
        self.assertEqual([fact["label"] for fact in event["preSessionContext"]], ["before"])

    def test_partial_amount_correction_blocks_only_conflicting_amount_uses(self):
        publication = ms("2025-07-03T09:00:00-04:00")
        cases = [({"amount_lower": 20000}, (20000, 15000), False),
                 ({"amount_upper": 500}, (1001, 500), False),
                 ({"amount_lower": 2000}, (2000, 15000), True),
                 ({"amount_upper": 10000}, (1001, 10000), True),
                 ({"amount_lower": 15000}, (15000, 15000), True)]
        for index, (fields, bounds, eligible) in enumerate(cases):
            version, rows = self.official(document=str(20031000 + index))
            row_id = rows[0]["id"]
            self.identities(version, row_id, publication)
            self.calendar(version, publication)
            original_evidence = self.disclosures.query_evidence(population=self.population)
            before = {perspective: next(event for event in self.view(perspective=perspective)["events"]
                                        if row_id in event["occurrenceIds"])
                      for perspective in ("public_information", "system_observation")}
            self.assertTrue(before["public_information"]["eligibility"]["primary_analysis"]["eligible"])
            self.assertTrue(before["system_observation"]["eligibility"]["watch_admission_prerequisites"]["eligible"])
            correction = self.assertion("correction", version, publication,
                                        occurrence_id=row_id, fields=fields)
            self.assertEqual(correction["fields"], fields)
            self.assertEqual(self.disclosures.query_evidence(population=self.population), original_evidence)
            for perspective, original in before.items():
                with self.subTest(fields=fields, perspective=perspective):
                    event = next(event for event in self.view(perspective=perspective)["events"]
                                 if row_id in event["occurrenceIds"])
                    self.assertEqual((event["fields"]["amountLower"], event["fields"]["amountUpper"]), bounds)
                    self.assertEqual(event["eligibility"]["amount_features"],
                                     {"eligible": eligible, "reasons": [] if eligible else ["amount_range_conflict"]})
                    for use in ("retention", "primary_analysis", "watch_admission_prerequisites", "latency"):
                        self.assertEqual(event["eligibility"][use], original["eligibility"][use])
                    for state in ("id", "identities", "publication", "anchor", "standing"):
                        self.assertEqual(event[state], original[state])

    def test_future_cited_evidence_cannot_be_backdated_by_assertion(self):
        publication = ms("2025-07-03T09:00:00-04:00")
        version, rows = self.official()
        future_version, _ = self.official("2025-07-07T12:00:00-04:00", document="20030444")
        self.assertion("identity", future_version, publication, occurrence_id=rows[0]["id"],
                       identity_type="security", identity_id="forbidden-later-fact", evidence_type="historical_listing",
                       valid_from="2020-01-01", listing_id="listing:future", calendar_id="XNYS")
        earlier = self.view("2025-07-03T10:00:00-04:00")["events"][0]
        self.assertEqual(earlier["identities"]["security"]["status"], "unresolved")
        self.assertIsNone(earlier["anchor"])

    def test_late_publication_narrowing_does_not_rewrite_original_date_boundary(self):
        version, _ = self.official(None)
        end = ms("2025-07-04T00:00:00-04:00")
        self.assertion("publication", version, end, artifact_version_id=version,
                       precision="date", raw_value="2025-07-03", timezone="America/New_York")
        self.assertion("publication", version, ms("2025-07-07T12:00:00-04:00"), artifact_version_id=version,
                       precision="exact", raw_value="2025-07-03T09:00:00-04:00")
        self.assertEqual(self.view("2025-07-03T10:00:00-04:00")["events"], [])
        self.assertEqual(self.view()["events"][0]["intrinsicBoundary"], end)

    def test_verified_amendment_attaches_only_scoped_changes_without_resetting_anchor(self):
        original, rows = self.official(count=2)
        original_time = ms("2025-07-03T09:00:00-04:00")
        for row in rows:
            self.identities(original, row["id"], original_time)
        self.calendar(original, original_time)
        amendment, amended_rows = self.official("2025-07-07T10:00:00-04:00", document="20030555", amount="$15,001 - $50,000")
        correction_time = ms("2025-07-07T10:00:00-04:00")
        self.assertion("relationship", amendment, correction_time, left_occurrence_id=rows[0]["id"],
                       right_occurrence_id=amended_rows[0]["id"], status="verified", relation="amendment",
                       citations=[{"artifact_version_id": version, "locator": "explicit original/correction row reference"}
                                  for version in [original, amendment]])
        self.assertion("correction", amendment, correction_time, occurrence_id=rows[0]["id"],
                       fields={"amount_lower": 15001, "amount_upper": 50000})
        before = self.view("2025-07-03T10:00:00-04:00")
        self.assertEqual(len(before["events"]), 2)
        after = self.view(mode="corrected_retrospective", original_as_of=before["asOf"])
        self.assertEqual(len(after["events"]), 2)
        changed = next(event for event in after["events"] if rows[0]["id"] in event["occurrenceIds"])
        untouched = next(event for event in after["events"] if rows[1]["id"] in event["occurrenceIds"])
        self.assertEqual(changed["fields"]["amountLower"], 15001)
        self.assertEqual(changed["intrinsicState"]["fields"]["amountLower"], 1001)
        self.assertEqual(untouched["fields"]["amountLower"], 1001)
        self.assertEqual(changed["anchor"]["open_at"], ms("2025-07-03T09:30:00-04:00"))

    def test_transitive_verification_cannot_collapse_identical_rows_in_one_artifact(self):
        first, rows = self.official(count=2)
        second, other = self.official(document="20030666")
        citations = [{"artifact_version_id": version, "locator": "row correspondence"} for version in [first, second]]
        self.assertion("relationship", first, ms("2025-07-03T12:00:00-04:00"),
                       left_occurrence_id=rows[0]["id"], right_occurrence_id=other[0]["id"], status="verified", citations=citations)
        with self.assertRaisesRegex(ValueError, "distinct occurrences"):
            self.assertion("relationship", first, ms("2025-07-03T12:00:00-04:00"),
                           left_occurrence_id=rows[1]["id"], right_occurrence_id=other[0]["id"], status="verified", citations=citations)

    def test_missing_fields_produce_nonexclusive_reasons_and_reconciled_denominators(self):
        self.official(None, count=2, transaction_date="", amount="")
        view = self.view()
        self.assertEqual(view["coverage"]["retainedOccurrences"], 2)
        self.assertEqual(view["coverage"]["primaryDisclosureEligible"], 0)
        self.assertEqual(view["coverage"]["reasonCounts"]["security_identity_unresolved"], 2)
        self.assertEqual(view["coverage"]["reasonCounts"]["publication_availability_unsupported"], 2)
        self.assertTrue(view["coverage"]["reasonsNonExclusive"])
        self.assertEqual(view["marketOutcomes"]["availability"], "unavailable")

    def test_recomputation_can_select_improved_processing_of_eligible_original_evidence(self):
        observed = ms("2025-07-03T12:00:00-04:00")
        with patch("disclosures.time.time", return_value=observed / 1000):
            result = self.disclosures.ingest_supporting_retrieval(RetrievedArtifact(
                population="test", source_name="kadoa", source_url="https://fixture.example/recompute",
                media_type="application/json", content=b'[{"ticker":" ABC ","transaction_date":" 2025-07-01 "}]',
                retrieved_at_ms=observed, purpose="manual", freshness_status="unknown", coverage_status="unknown",
            ))
        recorded = self.events.record_view(population="test", perspective="system_observation", as_of=observed)
        with patch("disclosures.time.time", return_value=self.now / 1000):
            self.disclosures.reprocess_artifact_version(result["artifactVersionId"], population="test",
                                                        extraction_method_version="2", normalization_method_version="2",
                                                        extracted_at_ms=self.now)
        public = self.view("2025-07-03T12:00:00-04:00")
        self.assertEqual(public["events"][0]["fields"]["transactionDate"], "2025-07-01")
        self.assertEqual(public["mode"], "historical_recomputation")
        system = self.view("2025-07-03T12:00:00-04:00", "system_observation")
        self.assertEqual(system["events"][0]["fields"]["transactionDate"], "2025-07-01")
        self.assertNotIn("transactionDate", recorded["events"][0]["fields"])
        self.assertEqual(self.view("2025-07-03T12:00:00-04:00", normalization_ids=public["selectedNormalizationIds"])["events"], public["events"])
        self.assertEqual(self.events.get_recorded_view(recorded["id"], population="test"), recorded)
        self.assertEqual(self.events.reproduce_recorded_view(recorded["id"], population="test")["output"], recorded)

    def test_row_order_invariance_of_event_projection_and_coverage(self):
        version, rows = self.official(count=2)
        for row in rows:
            self.identities(version, row["id"], ms("2025-07-03T09:00:00-04:00"))
        self.calendar(version, ms("2025-07-03T09:00:00-04:00"))
        expected = self.view()
        # Permute enumeration at the retained-evidence boundary; identities are the
        # existing occurrence IDs, never the caller's enumeration order.
        query = self.disclosures.query_evidence
        def permuted(*, population):
            retained = query(population=population)
            retained["artifacts"].reverse()
            for artifact in retained["artifacts"]:
                artifact["versions"].reverse()
                for retained_version in artifact["versions"]:
                    retained_version["rowOccurrences"].reverse()
            return retained
        with patch.object(DisclosureApplication, "query_evidence", side_effect=permuted):
            actual = self.view()
        self.assertEqual(actual, expected)

    def test_explicit_null_correction_blocks_only_dependent_use(self):
        version, rows = self.official()
        self.identities(version, rows[0]["id"], ms("2025-07-03T09:00:00-04:00"))
        self.calendar(version, ms("2025-07-03T09:00:00-04:00"))
        self.assertion("correction", version, ms("2025-07-07T10:00:00-04:00"),
                       occurrence_id=rows[0]["id"], fields={"amount_lower": None, "amount_upper": None})
        event = self.view(mode="corrected_retrospective", original_as_of=ms("2025-07-03T10:00:00-04:00"))["events"][0]
        self.assertFalse(event["eligibility"]["amount_features"]["eligible"])
        self.assertEqual(event["fields"]["transactionDirection"], "purchase")
        self.assertEqual(event["intrinsicState"]["fields"]["amountLower"], 1001)

    def test_publication_claim_cannot_leak_from_later_cited_evidence(self):
        version, _ = self.official(None)
        late_version, _ = self.official("2025-07-07T10:00:00-04:00", document="20030777")
        self.assertion("publication", late_version, ms("2025-07-03T09:00:00-04:00"),
                       artifact_version_id=version, precision="exact", raw_value="2025-07-03T09:00:00-04:00")
        self.assertEqual(self.view("2025-07-03T10:00:00-04:00")["events"], [])

    def test_supported_publication_after_asof_withholds_primary_eligibility(self):
        version, rows = self.official(None)
        early = ms("2025-07-03T12:00:00-04:00")
        self.assertion("publication", version, early, artifact_version_id=version,
                       precision="exact", raw_value="2025-07-07T10:00:00-04:00")
        self.identities(version, rows[0]["id"], early)
        self.calendar(version, early)
        event = self.view("2025-07-03T13:00:00-04:00")["events"][0]
        self.assertFalse(event["eligibility"]["primary_analysis"]["eligible"])
        self.assertIsNone(event["anchor"])

    def test_ambiguous_member_identity_and_late_retrieval_observations_remain_scoped(self):
        version, rows = self.official()
        public_at = ms("2025-07-03T09:00:00-04:00")
        self.identities(version, rows[0]["id"], public_at)
        self.assertion("identity", version, public_at, occurrence_id=rows[0]["id"], identity_type="member",
                       identity_id="other-member", evidence_type="verified_cross_source_mapping", valid_from="2020-01-01")
        earlier = self.view("2025-07-03T13:00:00-04:00")
        event = earlier["events"][0]
        self.assertEqual(event["identities"]["member"]["status"], "ambiguous")
        self.official(observed=ms("2025-07-07T12:00:00-04:00"))
        later = self.view("2025-07-03T13:00:00-04:00")
        self.assertEqual(event["provenance"]["rows"][0]["retrievalObservationIds"],
                         later["events"][0]["provenance"]["rows"][0]["retrievalObservationIds"])

    def test_date_interval_uses_timezone_dst_semantics(self):
        self.now = ms("2025-12-01T00:00:00+00:00")
        for index, (day, start, end, duration) in enumerate([
            ("2025-03-09", "2025-03-09T00:00:00-05:00", "2025-03-10T00:00:00-04:00", 23),
            ("2025-11-02", "2025-11-02T00:00:00-04:00", "2025-11-03T00:00:00-05:00", 25),
        ]):
            with self.subTest(day=day):
                version, _ = self.official(None, document=str(20030800 + index))
                self.assertion("publication", version, ms(end), artifact_version_id=version,
                               precision="date", raw_value=day, timezone="America/New_York")
                event = next(event for event in self.view("2025-12-01T00:00:00+00:00")["events"]
                             if event["provenance"]["rows"][0]["artifactVersionId"] == version)
                interval = event["publication"]["interval"]
                self.assertEqual((interval["start"], interval["endExclusive"]), (ms(start), ms(end)))
                self.assertEqual(interval["endExclusive"] - interval["start"], duration * 3600000)

    def test_unavailable_calendar_does_not_fall_back_to_weekdays(self):
        version, rows = self.official()
        self.identities(version, rows[0]["id"], ms("2025-07-03T09:00:00-04:00"))
        event = self.view()["events"][0]
        self.assertIsNone(event["anchor"])
        self.assertIn("session_anchor_unavailable", event["eligibility"]["primary_analysis"]["reasons"])

    def test_ticker_rename_preserves_separate_events_and_evidence_backed_shared_security(self):
        for document, asset in [("20030901", "Example Corp (OLD) [ST]"), ("20030902", "Example Corp (NEW) [ST]")]:
            version, rows = self.official(document=document, asset=asset)
            self.identities(version, rows[0]["id"], ms("2025-07-03T09:00:00-04:00"), security="stable-issuer")
        view = self.view()
        self.assertEqual(len(view["events"]), 2)
        self.assertEqual({event["identities"]["security"]["identity"]["identity_id"] for event in view["events"]}, {"stable-issuer"})
        self.assertEqual({event["provenance"]["rows"][0]["rawFields"]["asset"] for event in view["events"]},
                         {"Example Corp (OLD) [ST]", "Example Corp (NEW) [ST]"})

    def test_retrieval_only_can_support_watch_prerequisites_without_primary_publication_anchor(self):
        version, rows = self.official(None)
        self.identities(version, rows[0]["id"], ms("2025-07-03T12:00:00-04:00"))
        event = self.view(perspective="system_observation")["events"][0]
        self.assertTrue(event["eligibility"]["watch_admission_prerequisites"]["eligible"])
        self.assertFalse(event["eligibility"]["primary_analysis"]["eligible"])
        self.assertIsNone(event["publication"]["interval"])
        self.assertIsNone(event["intrinsicBoundary"])
        self.assertIsNone(event["anchor"])

    def test_future_normalization_selection_and_invalid_view_mode_are_rejected(self):
        observed = ms("2025-07-03T12:00:00-04:00")
        version, rows = self.official(observed=observed)
        normalization = rows[0]["normalizations"][0]["id"]
        with self.assertRaisesRegex(ValueError, "future source evidence"):
            self.view("2025-07-03T09:00:00-04:00", "system_observation", normalization_ids=[normalization])
        with self.assertRaises(ValueError):
            self.view(mode="unlabelled_current_state")

    def test_late_cited_publication_narrowing_preserves_supported_intrinsic_boundary(self):
        version, _ = self.official(None)
        end = ms("2025-07-04T00:00:00-04:00")
        self.assertion("publication", version, end, artifact_version_id=version,
                       precision="date", raw_value="2025-07-03", timezone="America/New_York")
        late_version, _ = self.official("2025-07-07T10:00:00-04:00", document="20030977")
        self.assertion("publication", late_version, ms("2025-07-03T09:00:00-04:00"),
                       artifact_version_id=version, precision="exact", raw_value="2025-07-03T09:00:00-04:00")
        original = next(event for event in self.view()["events"]
                        if event["provenance"]["rows"][0]["artifactVersionId"] == version)
        self.assertEqual(original["intrinsicBoundary"], end)

    def test_corrected_transaction_date_cannot_change_original_listing_anchor(self):
        version, rows = self.official(transaction_date="07/01/2025")
        public_at = ms("2025-07-03T09:00:00-04:00")
        self.identities(version, rows[0]["id"], public_at, security="original-security", valid_to="2025-07-02")
        self.calendar(version, public_at)
        self.assertion("identity", version, public_at, occurrence_id=rows[0]["id"], identity_type="security",
                       identity_id="other-security", evidence_type="historical_listing", valid_from="2025-07-02",
                       listing_id="listing:other", calendar_id="OTHER")
        self.assertion("calendar", version, public_at, calendar_id="OTHER", timezone="America/New_York",
            coverage_start=ms("2025-07-01T00:00:00-04:00"), coverage_end=ms("2025-07-09T00:00:00-04:00"),
            validation="validated_complete_regular_sessions", sessions=[
                {"session_date": "2025-07-03", "open_at": ms("2025-07-03T10:00:00-04:00"), "close_at": ms("2025-07-03T13:00:00-04:00")}])
        original = self.view()["events"][0]
        self.assertion("correction", version, ms("2025-07-07T10:00:00-04:00"), occurrence_id=rows[0]["id"],
                       fields={"transaction_date": "2025-07-02"})
        corrected = self.view(mode="corrected_retrospective", original_as_of=ms("2025-07-03T10:00:00-04:00"))["events"][0]
        self.assertEqual(corrected["anchor"], original["anchor"])
        self.assertEqual(corrected["fields"]["transactionDate"], "2025-07-02")

    def test_late_candidate_cannot_change_original_primary_eligibility(self):
        first, rows = self.official()
        second, other = self.official(document="20030988")
        public_at = ms("2025-07-03T09:00:00-04:00")
        for version, row in [(first, rows[0]), (second, other[0])]:
            self.identities(version, row["id"], public_at)
            self.calendar(version, public_at)
        before = self.view()
        self.assertTrue(all(event["eligibility"]["primary_analysis"]["eligible"] for event in before["events"]))
        self.assertion("relationship", first, ms("2025-07-07T10:00:00-04:00"), status="candidate",
                       left_occurrence_id=rows[0]["id"], right_occurrence_id=other[0]["id"],
                       citations=[{"artifact_version_id": version, "locator": "late uncertain correspondence"} for version in [first, second]])
        after = self.view()
        self.assertTrue(all(event["eligibility"]["primary_analysis"]["eligible"] for event in after["events"]))
        self.assertTrue(all(event["provenance"]["relationships"] for event in after["events"]))

    def test_filing_completeness_is_explicit_without_filing_size_exclusion(self):
        complete, _ = self.official(count=2)
        partial, _ = self.official(document="20030999", transaction_date="", amount="")
        view = self.view()
        filings = {filing["artifactVersionId"]: filing for filing in view["coverage"]["filings"]}
        self.assertEqual(filings[complete]["reportedRowOccurrences"], 2)
        self.assertEqual(filings[complete]["completeness"], "complete")
        self.assertEqual(filings[partial]["completeness"], "partial")
        self.assertEqual(filings[partial]["resolvedSecurities"], 0)
        self.assertEqual(filings[partial]["unresolvedSecurityOccurrences"], 1)
        self.assertTrue(all("filing_size" not in reason for reason in view["coverage"]["reasonCounts"]))

    def test_rejected_correspondence_does_not_block_later_scoped_remapping(self):
        first, rows = self.official(count=2)
        second, other = self.official(document="20030990")
        public_at = ms("2025-07-03T12:00:00-04:00")
        citations = [{"artifact_version_id": version, "locator": "explicit row correspondence"} for version in [first, second]]
        args = dict(left_occurrence_id=rows[0]["id"], right_occurrence_id=other[0]["id"], citations=citations)
        self.assertion("relationship", first, public_at, status="verified", **args)
        self.assertion("relationship", first, public_at, status="rejected", **args)
        self.assertion("relationship", first, public_at, status="verified", left_occurrence_id=rows[1]["id"],
                       right_occurrence_id=other[0]["id"], citations=citations)
        events = self.view(perspective="system_observation")["events"]
        self.assertEqual(len(events), 2)
        shared = next(event for event in events if other[0]["id"] in event["occurrenceIds"])
        self.assertEqual(set(shared["occurrenceIds"]), {rows[1]["id"], other[0]["id"]})

    def test_late_calendar_revision_cannot_replace_or_erase_original_anchor(self):
        version, rows = self.official()
        public_at = ms("2025-07-03T09:00:00-04:00")
        self.identities(version, rows[0]["id"], public_at)
        self.calendar(version, public_at)
        original = self.view()["events"][0]["anchor"]
        self.assertion("calendar", version, ms("2025-07-07T10:00:00-04:00"), calendar_id="XNYS", timezone="America/New_York",
            coverage_start=ms("2025-07-01T00:00:00-04:00"), coverage_end=ms("2025-07-09T00:00:00-04:00"),
            validation="validated_complete_regular_sessions", sessions=[
                {"session_date": "2025-07-03", "open_at": ms("2025-07-03T10:00:00-04:00"), "close_at": ms("2025-07-03T13:00:00-04:00")}])
        corrected = self.view(mode="corrected_retrospective", original_as_of=ms("2025-07-03T10:00:00-04:00"))["events"][0]
        self.assertEqual(corrected["anchor"], original)

    def test_later_publication_proof_has_a_separate_corrected_interpretation(self):
        version, rows = self.official(None, transaction_date="")
        late_version, _ = self.official("2025-07-07T10:00:00-04:00", document="20030991")
        late = ms("2025-07-07T10:00:00-04:00")
        self.assertion("publication", late_version, late, artifact_version_id=version,
                       precision="exact", raw_value="2025-07-03T09:00:00-04:00")
        self.identities(version, rows[0]["id"], late)
        self.calendar(version, late)
        original = next(event for event in self.view()["events"] if rows[0]["id"] in event["occurrenceIds"])
        self.assertIsNone(original["publication"]["interval"])
        self.assertIsNone(original["currentPublication"])
        corrected = next(event for event in self.view(mode="corrected_retrospective", original_as_of=ms("2025-07-03T13:00:00-04:00"))["events"]
                         if rows[0]["id"] in event["occurrenceIds"])
        self.assertEqual(corrected["currentPublication"]["availabilityBoundary"], ms("2025-07-03T09:00:00-04:00"))
        self.assertEqual(corrected["currentPublication"]["proofAvailableAt"], late)
        self.assertEqual(corrected["identities"]["security"]["status"], "resolved")
        self.assertIsNone(corrected["anchor"])
        self.assertIsNone(corrected["intrinsicBoundary"])
        self.assertEqual(corrected["retrospectiveAnchor"]["open_at"], ms("2025-07-03T09:30:00-04:00"))

    def test_conflicting_publication_instants_remain_ambiguous(self):
        version, _ = self.official()
        self.assertion("publication", version, ms("2025-07-03T10:00:00-04:00"),
                       artifact_version_id=version, precision="exact", raw_value="2025-07-03T10:00:00-04:00")
        event = self.view()["events"][0]
        self.assertIsNone(event["anchor"])
        self.assertIn("publication_availability_ambiguous", event["eligibility"]["primary_analysis"]["reasons"])
        self.assertEqual(len(event["publication"]["evidence"]), 2)

    def test_pinned_normalization_selection_does_not_erase_other_events(self):
        first, first_rows = self.official()
        second, second_rows = self.official(document="20030992")
        selected = first_rows[0]["normalizations"][0]["id"]
        view = self.view(normalization_ids=[selected])
        self.assertEqual({event["fields"]["transactionDirection"] for event in view["events"]}, {"purchase"})
        self.assertEqual(len(view["selectedNormalizationIds"]), 2)

    def test_public_relationship_ordering_cannot_transitively_collapse_same_version_rows(self):
        first, rows = self.official(count=2)
        second, other = self.official(document="20030993")
        citations = [{"artifact_version_id": version, "locator": "explicit row correspondence"} for version in [first, second]]
        args = dict(left_occurrence_id=rows[0]["id"], right_occurrence_id=other[0]["id"], citations=citations)
        earlier = ms("2025-07-03T09:00:00-04:00")
        self.assertion("relationship", first, earlier, status="verified", **args)
        self.assertion("relationship", first, ms("2025-07-07T10:00:00-04:00"), status="rejected", **args)
        self.assertion("relationship", first, earlier, status="verified", left_occurrence_id=rows[1]["id"],
                       right_occurrence_id=other[0]["id"], citations=citations)
        events = self.view("2025-07-03T13:00:00-04:00")["events"]
        self.assertEqual(len(events), 3)
        self.assertTrue(all(len(event["occurrenceIds"]) == 1 for event in events))
        self.assertTrue(all(event["occurrenceRelationshipStatus"] == "conflicting_verification" for event in events))
        self.assertTrue(all("occurrence_verification_conflict" in event["eligibility"]["primary_analysis"]["reasons"] for event in events))

    def test_forward_publication_claim_cannot_break_recorded_view_reproduction(self):
        first, _ = self.official()
        second, _ = self.official(None, document="20030994", observed=ms("2025-07-07T10:00:00-04:00"))
        self.assertion("publication", first, ms("2025-07-03T09:00:00-04:00"), artifact_version_id=second,
                       precision="exact", raw_value="2025-07-07T10:00:00-04:00")
        recorded = self.events.record_view(population="test", perspective="public_information", as_of=ms("2025-07-03T13:00:00-04:00"))
        self.assertEqual(len(recorded["events"]), 1)
        self.assertEqual(self.events.reproduce_recorded_view(recorded["id"], population="test")["output"], recorded)


if __name__ == "__main__":
    unittest.main()
