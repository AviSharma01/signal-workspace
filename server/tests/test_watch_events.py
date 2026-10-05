import sqlite3
import json
import subprocess
import sys
import unittest

from watch_events import WatchApplication
from disclosures import RetrievedArtifact
from tests import test_events


ms = test_events.ms


class WatchApplicationTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_events.EventApplicationTest()
        self.fixture.setUp()
        self.watch = WatchApplication(
            self.fixture.connection,
            lambda: self.fixture.now,
        )

    def tearDown(self):
        self.fixture.tearDown()

    def eligible_event(self, *, publication="2025-07-03T09:00:00-04:00", observed=None):
        version, rows = self.fixture.official(publication, observed=observed)
        evidence_time = ms(publication) if publication else self.fixture.now
        self.fixture.identities(version, rows[0]["id"], evidence_time)
        view = self.fixture.events.derive(population="test", perspective="system_observation",
                                          as_of=self.fixture.now)
        event = next(item for item in view["events"] if rows[0]["id"] in item["occurrenceIds"])
        return version, rows[0]["id"], event

    def reinstatement_citations(self, original):
        version, _ = self.fixture.official(None, document="20030009", observed=self.fixture.now,
                                           asset="Retained reinstatement evidence (ABC) [ST]")
        return [{"artifact_version_id": item, "locator": "explicit official reinstatement statement"}
                for item in (original, version)]

    def same_occurrence_representation(self, version, row, publication, *, document="20030002", status="verified"):
        other_version, other_rows = self.fixture.official(publication, document=document, observed=self.fixture.now)
        self.fixture.identities(other_version, other_rows[0]["id"], self.fixture.now)
        self.fixture.assertion("relationship", version, self.fixture.now, left_occurrence_id=row,
                               right_occurrence_id=other_rows[0]["id"], status=status, relation="same_occurrence",
                               citations=[{"artifact_version_id": item, "locator": "same original occurrence correspondence"}
                                          for item in (version, other_version)])
        return other_version, other_rows[0]["id"]

    def test_admission_is_independent_of_market_data_and_preserves_system_times(self):
        self.fixture.now = ms("2025-07-08T20:00:00-04:00")
        version, row, event = self.eligible_event(observed=ms("2025-07-03T12:00:00-04:00"))

        result = self.watch.admit(event["id"], population="test")

        admitted = result["watchEvent"]
        self.assertEqual(admitted["eventId"], event["id"])
        self.assertEqual(admitted["discoveredAt"], ms("2025-07-03T12:00:00-04:00"))
        self.assertEqual(admitted["officialEvidenceFirstObservedAt"], ms("2025-07-03T12:00:00-04:00"))
        self.assertEqual(admitted["verifiedAt"], self.fixture.now)
        self.assertEqual(admitted["admittedAt"], self.fixture.now)
        self.assertEqual(result["lastPersistedAssessment"]["evaluatedAt"], self.fixture.now)
        self.assertTrue(result["currentEvaluation"]["activeEligibility"]["eligible"])
        self.assertNotIn("market", str(result).lower())

    def test_exact_publication_expires_strictly_at_thirty_local_calendar_dates(self):
        self.fixture.now = ms("2025-07-08T20:00:00-04:00")
        _, _, event = self.eligible_event()
        result = self.watch.admit(event["id"], population="test")
        expiry = ms("2025-08-02T09:00:00-04:00")
        self.assertEqual(result["currentEvaluation"]["expirySupport"]["expiresAt"], expiry)

        self.fixture.now = expiry - 1
        self.assertTrue(self.watch.get(result["watchEvent"]["id"], population="test")["currentEvaluation"]["activeEligibility"]["eligible"])
        self.fixture.now = expiry
        current = self.watch.get(result["watchEvent"]["id"], population="test")["currentEvaluation"]
        self.assertFalse(current["activeEligibility"]["eligible"])
        self.assertEqual(current["recency"]["status"], "expired")

    def test_date_only_publication_stays_interval_valued_and_straddling_withholds_activity(self):
        self.fixture.now = ms("2025-07-08T20:00:00-04:00")
        version, rows = self.fixture.official(None)
        publication_end = ms("2025-07-04T00:00:00-04:00")
        self.fixture.assertion("publication", version, publication_end, artifact_version_id=version,
                               precision="date", raw_value="2025-07-03", timezone="America/New_York")
        self.fixture.identities(version, rows[0]["id"], publication_end)
        event = self.fixture.view(perspective="system_observation")["events"][0]
        admitted = self.watch.admit(event["id"], population="test")
        expiry = admitted["currentEvaluation"]["expirySupport"]
        self.assertEqual(expiry["status"], "interval")
        self.assertEqual(expiry["earliestExpiryAt"], ms("2025-08-02T00:00:00-04:00"))
        self.assertEqual(expiry["latestExpiryAt"], ms("2025-08-03T00:00:00-04:00") - 1)

        self.fixture.now = ms("2025-08-02T12:00:00-04:00")
        uncertain = self.watch.get(admitted["watchEvent"]["id"], population="test")["currentEvaluation"]
        self.assertEqual(uncertain["recency"]["status"], "expiry_uncertain")
        self.assertFalse(uncertain["activeEligibility"]["eligible"])
        self.assertIn("expiry_uncertain", uncertain["lifecycleReasons"])
        self.fixture.now = ms("2025-08-03T00:00:00-04:00")
        expired = self.watch.get(admitted["watchEvent"]["id"], population="test")["currentEvaluation"]
        self.assertEqual(expired["recency"]["status"], "expired")

    def test_unknown_publication_age_allows_admission_but_withholds_active_eligibility(self):
        _, _, event = self.eligible_event(publication=None)
        result = self.watch.admit(event["id"], population="test")
        current = result["currentEvaluation"]
        self.assertEqual(current["recency"]["status"], "publication_age_unknown")
        self.assertEqual(current["expirySupport"]["status"], "unsupported")
        self.assertFalse(current["activeEligibility"]["eligible"])

    def test_dst_ambiguous_expiry_uses_earlier_occurrence(self):
        self.fixture.now = ms("2025-10-10T12:00:00-04:00")
        _, _, event = self.eligible_event(publication="2025-10-03T01:30:00-04:00")
        result = self.watch.admit(event["id"], population="test")
        self.assertEqual(result["currentEvaluation"]["expirySupport"]["expiresAt"],
                         ms("2025-11-02T01:30:00-04:00"))

    def test_dst_nonexistent_expiry_uses_first_valid_instant(self):
        self.fixture.now = ms("2025-02-10T12:00:00-05:00")
        _, _, event = self.eligible_event(publication="2025-02-07T02:30:00-05:00",
                                          observed=ms("2025-02-07T12:00:00-05:00"))
        result = self.watch.admit(event["id"], population="test")
        self.assertEqual(result["currentEvaluation"]["expirySupport"]["expiresAt"],
                         ms("2025-03-09T03:00:00-04:00"))

    def test_old_event_can_be_admitted_after_expiry_without_becoming_active(self):
        self.fixture.now = ms("2025-09-15T12:00:00-04:00")
        _, _, event = self.eligible_event(publication="2025-07-03T09:00:00-04:00",
                                          observed=ms("2025-09-15T10:00:00-04:00"))
        result = self.watch.admit(event["id"], population="test")
        self.assertEqual(result["currentEvaluation"]["recency"]["status"], "expired")
        self.assertFalse(result["currentEvaluation"]["activeEligibility"]["eligible"])
        self.assertEqual(result["lifecycleHistory"][0]["evaluatedAt"], self.fixture.now)

    def test_startup_recovery_records_actual_observation_not_fabricated_expiry_time(self):
        self.fixture.now = ms("2025-07-08T20:00:00-04:00")
        _, _, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        expiry = admitted["currentEvaluation"]["expirySupport"]["expiresAt"]
        recovery_time = ms("2025-08-05T11:17:00-04:00")
        self.fixture.now = recovery_time
        restarted = WatchApplication(self.fixture.connection, lambda: self.fixture.now)
        self.assertEqual(restarted.reevaluate_all(population="test", trigger="startup_recovery"), 1)
        result = restarted.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(len(result["lifecycleHistory"]), 2)
        transition = result["lifecycleHistory"][-1]
        self.assertEqual(transition["evaluatedAt"], recovery_time)
        self.assertNotEqual(transition["evaluatedAt"], expiry)
        self.assertEqual(transition["transitionReasons"], ["expired"])

    def test_later_publication_evidence_establishes_clock_without_backdating(self):
        self.fixture.now = ms("2025-07-08T20:00:00-04:00")
        version, _, event = self.eligible_event(publication=None)
        admitted = self.watch.admit(event["id"], population="test")
        first = admitted["lastPersistedAssessment"]
        self.fixture.now = ms("2025-07-09T10:00:00-04:00")
        self.fixture.assertion("publication", version, ms("2025-07-03T09:00:00-04:00"),
                               artifact_version_id=version, precision="exact",
                               raw_value="2025-07-03T09:00:00-04:00")
        self.assertEqual(self.watch.reevaluate_all(population="test", trigger="evidence_change"), 0)
        result = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(first["recency"]["status"], "publication_age_unknown")
        self.assertEqual(result["lastPersistedAssessment"]["recency"]["status"], "within_window")
        self.assertEqual(result["lifecycleHistory"][-1]["evaluatedAt"], self.fixture.now)
        self.assertEqual(result["watchEvent"]["admittedAt"], ms("2025-07-08T20:00:00-04:00"))

    def test_withdrawal_unresolved_failed_criteria_and_reinstatement_remain_distinct(self):
        self.fixture.now = ms("2025-07-08T20:00:00-04:00")
        version, row, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        watch_id = admitted["watchEvent"]["id"]

        self.fixture.now = ms("2025-07-09T10:00:00-04:00")
        self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row,
                               fields={}, standing="withdrawn")
        self.watch.reevaluate_all(population="test", trigger="evidence_change")
        withdrawn = self.watch.get(watch_id, population="test")
        self.assertEqual(withdrawn["currentEvaluation"]["evidenceStanding"]["status"], "withdrawn")
        self.assertEqual(withdrawn["lifecycleHistory"][-1]["transitionReasons"], ["withdrawn"])

        self.fixture.now = ms("2025-07-10T10:00:00-04:00")
        self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row,
                               fields={}, standing="unresolved")
        self.watch.reevaluate_all(population="test", trigger="evidence_change")
        unresolved = self.watch.get(watch_id, population="test")
        self.assertEqual(unresolved["currentEvaluation"]["evidenceStanding"]["status"], "unresolved")
        self.assertEqual(unresolved["lifecycleHistory"][-1]["transitionReasons"], ["standing_unresolved"])

        self.fixture.now = ms("2025-07-11T10:00:00-04:00")
        self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row,
                               fields={"asset_class": "out_of_scope"}, standing="supported",
                               standing_resolution="reinstatement", citations=self.reinstatement_citations(version))
        self.watch.reevaluate_all(population="test", trigger="evidence_change")
        failed = self.watch.get(watch_id, population="test")
        current = failed["currentEvaluation"]
        self.assertEqual(current["evidenceStanding"]["status"], "supported")
        self.assertFalse(current["admissionCriteria"]["satisfied"])
        self.assertIn("individual_equity_unresolved_or_out_of_scope", current["admissionCriteria"]["reasons"])
        self.assertIn("admission_criteria_failed", failed["lifecycleHistory"][-1]["transitionReasons"])

        self.fixture.now = ms("2025-07-12T10:00:00-04:00")
        self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row,
                               fields={"asset_class": "individual_public_equity"}, standing="supported")
        self.watch.reevaluate_all(population="test", trigger="evidence_change")
        reinstated = self.watch.get(watch_id, population="test")
        self.assertTrue(reinstated["currentEvaluation"]["activeEligibility"]["eligible"])
        self.assertEqual(reinstated["lifecycleHistory"][-1]["transitionReasons"], ["admission_criteria_restored"])

    def test_withdrawal_reinstatement_after_expiry_preserves_overlapping_expiry_reason_and_clock(self):
        self.fixture.now = ms("2025-07-08T20:00:00-04:00")
        version, row, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        original_expiry = admitted["currentEvaluation"]["expirySupport"]["expiresAt"]
        self.fixture.now = ms("2025-07-20T10:00:00-04:00")
        self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row,
                               fields={}, standing="withdrawn")
        self.watch.reevaluate_all(population="test", trigger="evidence_change")
        self.fixture.now = ms("2025-08-05T10:00:00-04:00")
        self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row,
                               fields={}, standing="supported", standing_resolution="reinstatement",
                               citations=self.reinstatement_citations(version))
        self.watch.reevaluate_all(population="test", trigger="evidence_change")
        result = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertFalse(result["currentEvaluation"]["activeEligibility"]["eligible"])
        self.assertEqual(result["currentEvaluation"]["expirySupport"]["expiresAt"], original_expiry)
        self.assertIn("expired", result["currentEvaluation"]["lifecycleReasons"])
        self.assertIn("reinstated", result["lifecycleHistory"][-1]["transitionReasons"])

    def test_unchanged_reprocessing_and_admission_retry_are_idempotent(self):
        _, _, event = self.eligible_event()
        first = self.watch.admit(event["id"], population="test")
        second = self.watch.admit(event["id"], population="test")
        self.assertEqual(first["watchEvent"]["id"], second["watchEvent"]["id"])
        self.assertEqual(self.watch.reevaluate_all(population="test", trigger="evidence_change"), 0)
        result = self.watch.get(first["watchEvent"]["id"], population="test")
        self.assertEqual(len(result["lifecycleHistory"]), 1)
        self.assertEqual(len(self.watch.list(population="test")["watchEvents"]), 1)

    def test_failed_uncommitted_admission_leaves_no_watch_or_history_and_retry_succeeds(self):
        _, _, event = self.eligible_event()
        with self.fixture.connection() as conn:
            conn.execute("CREATE TRIGGER fail_watch_history BEFORE INSERT ON watch_lifecycle_history "
                         "BEGIN SELECT RAISE(ABORT, 'fixture failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.watch.admit(event["id"], population="test")
        self.assertEqual(self.watch.list(population="test")["state"], "empty")
        with self.fixture.connection() as conn:
            conn.execute("DROP TRIGGER fail_watch_history")
        result = self.watch.admit(event["id"], population="test")
        self.assertEqual(len(result["lifecycleHistory"]), 1)

    def test_stale_stored_assessment_cannot_authorize_active_only_action(self):
        self.fixture.now = ms("2025-07-08T20:00:00-04:00")
        _, _, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        watch_id = admitted["watchEvent"]["id"]
        self.fixture.now = ms("2025-08-05T10:00:00-04:00")
        displayed = self.watch.get(watch_id, population="test")
        self.assertTrue(displayed["lastPersistedAssessment"]["activeEligibility"]["eligible"])
        self.assertFalse(displayed["currentEvaluation"]["activeEligibility"]["eligible"])
        self.assertTrue(displayed["lastPersistedAssessmentIsStale"])
        self.assertTrue(displayed["currentDiffersFromLastPersisted"])

        authorization = self.watch.authorize_active_action(watch_id, population="test")
        self.assertFalse(authorization["authorized"])
        persisted = self.watch.get(watch_id, population="test")
        self.assertEqual(persisted["lifecycleHistory"][-1]["trigger"], "pre_active_action")
        self.assertFalse(persisted["lastPersistedAssessment"]["activeEligibility"]["eligible"])

    def test_recorded_reproduction_recomputation_and_corrected_retrospective_are_distinct(self):
        self.fixture.now = ms("2025-07-08T20:00:00-04:00")
        version, _, event = self.eligible_event(publication=None)
        admitted = self.watch.admit(event["id"], population="test")
        assessment_id = admitted["lifecycleHistory"][0]["id"]
        self.fixture.now = ms("2025-07-09T10:00:00-04:00")
        self.fixture.assertion("publication", version, ms("2025-07-03T09:00:00-04:00"),
                               artifact_version_id=version, precision="exact",
                               raw_value="2025-07-03T09:00:00-04:00")

        reproduced = self.watch.reproduce(assessment_id, population="test")
        recomputed = self.watch.historical_recompute(assessment_id, population="test")
        corrected = self.watch.corrected_retrospective(assessment_id, population="test", as_of=self.fixture.now)
        self.assertEqual(reproduced["recordType"], "deterministic_reproduction")
        self.assertEqual(recomputed["recordType"], "historical_recomputation")
        self.assertEqual(corrected["recordType"], "corrected_retrospective")
        self.assertEqual(reproduced["output"]["recency"]["status"], "publication_age_unknown")
        self.assertEqual(recomputed["output"]["recency"]["status"], "publication_age_unknown")
        self.assertEqual(corrected["output"]["recency"]["status"], "within_window")
        recorded = self.watch.get(admitted["watchEvent"]["id"], population="test")["lifecycleHistory"][0]
        self.assertEqual(recorded["assessment"]["recency"]["status"], "publication_age_unknown")

    def test_source_local_interval_ending_at_dst_fold_uses_every_supported_publication_time(self):
        self.fixture.now = ms("2025-11-02T12:00:00-05:00")
        version, rows = self.fixture.official(None)
        self.fixture.assertion("publication", version, self.fixture.now, artifact_version_id=version,
                               precision="date", raw_value="2025-11-01", timezone="America/Regina")
        self.fixture.identities(version, rows[0]["id"], self.fixture.now)
        result = self.watch.admit(f"event:{rows[0]['id']}", population="test")
        support = result["currentEvaluation"]["expirySupport"]
        self.assertEqual(support["earliestExpiryAt"], ms("2025-12-01T02:00:00-05:00"))
        self.assertEqual(support["latestExpiryAt"], ms("2025-12-02T02:00:00-05:00") - 1)
        self.fixture.now = ms("2025-12-02T01:30:00-05:00")
        current = self.watch.get(result["watchEvent"]["id"], population="test")["currentEvaluation"]
        self.assertEqual(current["recency"]["status"], "expiry_uncertain")
        self.assertFalse(current["activeEligibility"]["eligible"])

    def test_repeating_identical_correction_evidence_does_not_duplicate_transition(self):
        version, row, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        for day in (9, 10):
            self.fixture.now = ms(f"2025-07-{day:02d}T10:00:00-04:00")
            self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row,
                                   fields={}, standing="withdrawn")
        result = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(len(result["lifecycleHistory"]), 2)
        self.assertEqual(result["lifecycleHistory"][-1]["transitionReasons"], ["withdrawn"])

    def test_withdrawn_and_expired_reasons_overlap_without_erasing_standing(self):
        version, row, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-08-05T10:00:00-04:00")
        self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row,
                               fields={}, standing="withdrawn")
        result = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(result["currentEvaluation"]["lifecycleReasons"], ["evidence_withdrawn", "expired"])
        self.assertEqual(result["lifecycleHistory"][-1]["transitionReasons"], ["expired", "withdrawn"])

    def test_known_expiry_reevaluation_persists_at_boundary_and_retries_once(self):
        _, _, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        boundary = admitted["currentEvaluation"]["expirySupport"]["expiresAt"]
        self.assertEqual(self.watch.next_evaluation_at(population="test"), boundary)
        self.fixture.now = boundary
        self.assertEqual(self.watch.reevaluate_due(population="test"), 1)
        self.assertEqual(self.watch.reevaluate_due(population="test"), 0)
        result = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(result["lifecycleHistory"][-1]["evaluatedAt"], boundary)
        self.assertEqual(result["lifecycleHistory"][-1]["trigger"], "known_expiry")
        self.assertIsNone(self.watch.next_evaluation_at(population="test"))

    def test_failed_transition_keeps_prior_history_and_recovery_uses_actual_later_time(self):
        version, row, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        with self.fixture.connection() as conn:
            conn.execute("CREATE TRIGGER fail_watch_history BEFORE INSERT ON watch_lifecycle_history "
                         "BEGIN SELECT RAISE(ABORT, 'fixture failure'); END")
        self.fixture.now = ms("2025-07-09T10:00:00-04:00")
        with self.assertRaises(sqlite3.IntegrityError):
            self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row,
                                   fields={}, standing="withdrawn")
        pending = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(len(pending["lifecycleHistory"]), 1)
        self.assertEqual(pending["currentEvaluation"]["evidenceStanding"]["status"], "withdrawn")
        self.assertTrue(pending["currentDiffersFromLastPersisted"])
        with self.fixture.connection() as conn:
            conn.execute("DROP TRIGGER fail_watch_history")
        self.fixture.now = ms("2025-07-10T12:30:00-04:00")
        self.assertEqual(self.watch.reevaluate_all(population="test", trigger="startup_recovery"), 1)
        recovered = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(recovered["lifecycleHistory"][-1]["evaluatedAt"], self.fixture.now)

    def test_process_crash_after_insert_before_commit_rolls_back_and_recovers_without_duplicates(self):
        _, _, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        with self.fixture.connection() as conn:
            conn.execute("CREATE TRIGGER crash_watch_history AFTER INSERT ON watch_lifecycle_history "
                         "BEGIN SELECT fixture_crash(); END")
        crash_time = ms("2025-08-03T10:00:00-04:00")
        script = '''
import os, sqlite3, sys
from contextlib import contextmanager
from watch_events import WatchApplication
@contextmanager
def connection():
    conn = sqlite3.connect(sys.argv[1])
    conn.row_factory = sqlite3.Row
    conn.create_function("fixture_crash", 0, lambda: os._exit(73))
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()
WatchApplication(connection, lambda: int(sys.argv[2])).reevaluate_all(population="test", trigger="startup_recovery")
'''
        crashed = subprocess.run([sys.executable, "-c", script, str(self.fixture.path), str(crash_time)],
                                 capture_output=True, text=True, timeout=20)
        self.assertEqual(crashed.returncode, 73, crashed.stderr)
        self.fixture.now = ms("2025-08-05T10:00:00-04:00")
        observed = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(len(observed["lifecycleHistory"]), 1)
        with self.fixture.connection() as conn:
            conn.execute("DROP TRIGGER crash_watch_history")
        self.watch.reevaluate_all(population="test", trigger="startup_recovery")
        self.watch.reevaluate_all(population="test", trigger="startup_recovery")
        recovered = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(len(recovered["lifecycleHistory"]), 2)
        self.assertEqual(recovered["lifecycleHistory"][-1]["evaluatedAt"], self.fixture.now)

    def test_later_verified_amendment_cannot_move_original_publication_clock(self):
        version, row, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        expiry = admitted["currentEvaluation"]["expirySupport"]["expiresAt"]
        self.fixture.now = ms("2025-07-20T10:00:00-04:00")
        amended_version, amended_rows = self.fixture.official("2025-07-19T09:00:00-04:00", document="20030002",
                                                             observed=self.fixture.now)
        self.fixture.assertion("relationship", version, self.fixture.now, left_occurrence_id=row,
                               right_occurrence_id=amended_rows[0]["id"], status="verified", relation="amendment",
                               citations=[{"artifact_version_id": item, "locator": "explicit amendment correspondence"}
                                          for item in (version, amended_version)])
        self.fixture.assertion("correction", amended_version, self.fixture.now, occurrence_id=row,
                               fields={"transaction_direction": "sale"})
        result = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(result["currentEvaluation"]["expirySupport"]["expiresAt"], expiry)
        retried = self.watch.admit(result["currentEvent"]["id"], population="test")
        self.assertEqual(retried["watchEvent"]["id"], admitted["watchEvent"]["id"])

    def test_earlier_verified_same_occurrence_shortens_clock_and_denies_current_action(self):
        self.fixture.now = ms("2025-07-10T12:00:00-04:00")
        version, row, event = self.eligible_event(publication="2025-07-09T09:00:00-04:00",
                                                observed=self.fixture.now)
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-08-03T12:00:00-04:00")
        earlier_version, earlier_rows = self.fixture.official("2025-07-03T09:00:00-04:00",
                                                             document="20030002", observed=self.fixture.now)
        self.fixture.identities(earlier_version, earlier_rows[0]["id"], self.fixture.now)
        self.fixture.assertion("relationship", version, self.fixture.now, left_occurrence_id=row,
                               right_occurrence_id=earlier_rows[0]["id"], status="verified", relation="same_occurrence",
                               citations=[{"artifact_version_id": item, "locator": "verified same original occurrence"}
                                          for item in (version, earlier_version)])

        current = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(current["currentEvaluation"]["expirySupport"]["expiresAt"],
                         ms("2025-08-02T09:00:00-04:00"))
        self.assertFalse(self.watch.authorize_active_action(admitted["watchEvent"]["id"], population="test")["authorized"])
        self.assertEqual(current["lifecycleHistory"][-1]["evaluatedAt"], self.fixture.now)
        self.assertEqual(current["lifecycleHistory"][0], admitted["lifecycleHistory"][0])

    def test_earlier_same_occurrence_replay_preserves_original_evidence_boundary(self):
        self.fixture.now = ms("2025-07-10T12:00:00-04:00")
        version, row, event = self.eligible_event(publication="2025-07-09T09:00:00-04:00",
                                                observed=self.fixture.now)
        admitted = self.watch.admit(event["id"], population="test")
        record = admitted["lifecycleHistory"][0]
        self.fixture.now = ms("2025-08-03T12:00:00-04:00")
        self.same_occurrence_representation(version, row, "2025-07-03T09:00:00-04:00")
        self.same_occurrence_representation(version, row, "2025-07-19T09:00:00-04:00", document="20030003")

        self.assertEqual(self.watch.recorded_assessment(admitted["watchEvent"]["id"], record["id"], population="test"), record)
        self.assertEqual(self.watch.reproduce(record["id"], population="test")["output"], record["assessment"])
        recomputed = self.watch.historical_recompute(record["id"], population="test")
        self.assertEqual(recomputed["output"]["expirySupport"]["expiresAt"], ms("2025-08-08T09:00:00-04:00"))
        self.assertTrue(recomputed["output"]["activeEligibility"]["eligible"])
        corrected = self.watch.corrected_retrospective(record["id"], population="test", as_of=self.fixture.now)
        self.assertEqual(corrected["output"]["expirySupport"]["expiresAt"], ms("2025-08-02T09:00:00-04:00"))
        self.assertEqual(corrected["output"]["evaluatedAt"], record["evaluatedAt"])
        current = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertFalse(current["currentEvaluation"]["activeEligibility"]["eligible"])
        self.assertEqual(current["lifecycleHistory"][-1]["evaluatedAt"], self.fixture.now)
        self.assertEqual(current["lifecycleHistory"][-1]["persistedAt"], self.fixture.now)

    def test_unverified_earlier_copy_cannot_change_clock_and_later_verified_copy_cannot_extend_it(self):
        version, row, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        expiry = ms("2025-08-02T09:00:00-04:00")
        self.fixture.now = ms("2025-07-20T12:00:00-04:00")
        self.same_occurrence_representation(version, row, "2025-07-01T09:00:00-04:00", status="candidate")
        current = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(current["currentEvaluation"]["expirySupport"]["expiresAt"], expiry)
        self.same_occurrence_representation(version, row, "2025-07-19T09:00:00-04:00", document="20030003")
        self.fixture.now = ms("2025-08-03T12:00:00-04:00")
        current = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(current["currentEvaluation"]["expirySupport"]["expiresAt"], expiry)
        self.assertFalse(self.watch.authorize_active_action(admitted["watchEvent"]["id"], population="test")["authorized"])

    def test_amendment_earlier_publication_and_correction_are_not_original_clocks(self):
        version, row, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-07-20T12:00:00-04:00")
        amendment, amendment_rows = self.fixture.official("2025-07-01T09:00:00-04:00",
                                                          document="20030002", observed=self.fixture.now)
        self.fixture.assertion("relationship", version, self.fixture.now, left_occurrence_id=row,
                               right_occurrence_id=amendment_rows[0]["id"], status="verified", relation="amendment",
                               citations=[{"artifact_version_id": item, "locator": "explicit amendment correspondence"}
                                          for item in (version, amendment)])
        self.fixture.assertion("correction", amendment, self.fixture.now, occurrence_id=row,
                               fields={"transaction_direction": "sale"})
        current = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(current["currentEvaluation"]["expirySupport"]["expiresAt"], ms("2025-08-02T09:00:00-04:00"))
        self.assertEqual(current["currentEvent"]["fields"]["transactionDirection"], "sale")

    def test_new_reported_occurrence_has_separate_watch_and_publication_clock(self):
        version, row, event = self.eligible_event()
        original = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-07-20T12:00:00-04:00")
        other, other_rows = self.fixture.official("2025-07-19T09:00:00-04:00", document="20030002",
                                                 observed=self.fixture.now, transaction_date="07/15/2025")
        self.fixture.identities(other, other_rows[0]["id"], self.fixture.now)
        new = self.watch.admit(f"event:{other_rows[0]['id']}", population="test")
        self.assertNotEqual(new["watchEvent"]["id"], original["watchEvent"]["id"])
        self.assertEqual(new["currentEvaluation"]["expirySupport"]["expiresAt"], ms("2025-08-18T09:00:00-04:00"))
        current = self.watch.get(original["watchEvent"]["id"], population="test")
        self.assertEqual(current["currentEvaluation"]["expirySupport"]["expiresAt"], ms("2025-08-02T09:00:00-04:00"))

    def test_earlier_date_only_same_occurrence_keeps_expiry_uncertainty(self):
        self.fixture.now = ms("2025-07-10T12:00:00-04:00")
        version, row, event = self.eligible_event(publication="2025-07-09T09:00:00-04:00",
                                                observed=self.fixture.now)
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-08-02T12:00:00-04:00")
        earlier, earlier_row = self.same_occurrence_representation(version, row, None)
        self.fixture.assertion("publication", earlier, ms("2025-07-04T00:00:00-04:00"),
                               artifact_version_id=earlier, precision="date", raw_value="2025-07-03", timezone="America/New_York")
        current = self.watch.get(admitted["watchEvent"]["id"], population="test")["currentEvaluation"]
        self.assertEqual(current["expirySupport"]["status"], "interval")
        self.assertEqual(current["expirySupport"]["earliestExpiryAt"], ms("2025-08-02T00:00:00-04:00"))
        self.assertEqual(current["expirySupport"]["latestExpiryAt"], ms("2025-08-03T00:00:00-04:00") - 1)
        self.assertEqual(current["recency"]["status"], "expiry_uncertain")
        self.assertFalse(current["activeEligibility"]["eligible"])

    def test_exact_same_occurrence_copy_tightens_date_interval_upper_bound(self):
        self.fixture.now = ms("2025-07-10T12:00:00-04:00")
        version, rows = self.fixture.official(None)
        row = rows[0]["id"]
        self.fixture.assertion("publication", version, ms("2025-07-04T00:00:00-04:00"),
                               artifact_version_id=version, precision="date", raw_value="2025-07-03", timezone="America/New_York")
        self.fixture.identities(version, row, self.fixture.now)
        admitted = self.watch.admit(f"event:{row}", population="test")
        self.fixture.now = ms("2025-08-02T12:00:00-04:00")
        self.same_occurrence_representation(version, row, "2025-07-03T09:00:00-04:00")
        current = self.watch.get(admitted["watchEvent"]["id"], population="test")["currentEvaluation"]
        self.assertEqual(current["recency"]["status"], "expired")
        self.assertEqual(current["expirySupport"]["status"], "interval")
        self.assertEqual(current["expirySupport"]["earliestExpiryAt"], ms("2025-08-02T00:00:00-04:00"))
        self.assertEqual(current["expirySupport"]["latestExpiryAt"], ms("2025-08-02T09:00:00-04:00"))
        self.assertFalse(current["activeEligibility"]["eligible"])
        self.assertEqual(self.watch.reproduce(admitted["lifecycleHistory"][0]["id"], population="test")["output"],
                         admitted["lastPersistedAssessment"])

    def test_verified_copy_of_amendment_cannot_establish_original_publication_clock(self):
        self.fixture.now = ms("2025-07-10T12:00:00-04:00")
        version, row, event = self.eligible_event(publication=None, observed=self.fixture.now)
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-07-22T12:00:00-04:00")
        amendment, amendment_rows = self.fixture.official("2025-07-20T09:00:00-04:00", document="20030002",
                                                          observed=self.fixture.now)
        self.fixture.identities(amendment, amendment_rows[0]["id"], self.fixture.now)
        self.fixture.assertion("relationship", version, self.fixture.now, left_occurrence_id=row,
                               right_occurrence_id=amendment_rows[0]["id"], status="verified", relation="amendment",
                               citations=[{"artifact_version_id": item, "locator": "explicit original/amendment correspondence"}
                                          for item in (version, amendment)])
        self.same_occurrence_representation(amendment, amendment_rows[0]["id"], "2025-07-21T09:00:00-04:00",
                                            document="20030003")
        current = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(current["currentEvaluation"]["recency"]["status"], "publication_age_unknown")
        self.assertEqual(current["currentEvaluation"]["expirySupport"]["status"], "unsupported")
        self.assertFalse(self.watch.authorize_active_action(admitted["watchEvent"]["id"], population="test")["authorized"])
        self.assertEqual(self.watch.reproduce(admitted["lifecycleHistory"][0]["id"], population="test")["output"],
                         admitted["lastPersistedAssessment"])

    def test_later_official_relationship_can_establish_admission_representation_was_an_amendment(self):
        self.fixture.now = ms("2025-07-22T12:00:00-04:00")
        amendment, amendment_row, event = self.eligible_event(publication="2025-07-20T09:00:00-04:00",
                                                             observed=self.fixture.now)
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-07-23T12:00:00-04:00")
        original, original_rows = self.fixture.official(None, document="20030002", observed=self.fixture.now)
        self.fixture.identities(original, original_rows[0]["id"], self.fixture.now)
        self.fixture.assertion("relationship", original, self.fixture.now, left_occurrence_id=original_rows[0]["id"],
                               right_occurrence_id=amendment_row, status="verified", relation="amendment",
                               citations=[{"artifact_version_id": item, "locator": "official identification of original and amendment"}
                                          for item in (original, amendment)])
        current = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(current["currentEvaluation"]["recency"]["status"], "publication_age_unknown")
        self.assertFalse(self.watch.authorize_active_action(admitted["watchEvent"]["id"], population="test")["authorized"])
        self.assertEqual(current["lifecycleHistory"][0], admitted["lifecycleHistory"][0])
        self.assertEqual(current["lifecycleHistory"][-1]["evaluatedAt"], self.fixture.now)
        self.assertEqual(self.watch.reproduce(admitted["lifecycleHistory"][0]["id"], population="test")["output"],
                         admitted["lastPersistedAssessment"])
        record_id = admitted["lifecycleHistory"][0]["id"]
        self.assertTrue(self.watch.historical_recompute(record_id, population="test")["output"]["activeEligibility"]["eligible"])
        corrected = self.watch.corrected_retrospective(record_id, population="test", as_of=self.fixture.now)
        self.assertEqual(corrected["output"]["recency"]["status"], "publication_age_unknown")
        self.assertFalse(corrected["output"]["activeEligibility"]["eligible"])

    def test_earlier_same_occurrence_failed_transition_recovers_at_actual_time(self):
        self.fixture.now = ms("2025-07-10T12:00:00-04:00")
        version, row, event = self.eligible_event(publication="2025-07-09T09:00:00-04:00",
                                                observed=self.fixture.now)
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-08-03T12:00:00-04:00")
        earlier, earlier_rows = self.fixture.official("2025-07-03T09:00:00-04:00",
                                                      document="20030002", observed=self.fixture.now)
        self.fixture.identities(earlier, earlier_rows[0]["id"], self.fixture.now)
        with self.fixture.connection() as conn:
            conn.execute("CREATE TRIGGER fail_watch_history BEFORE INSERT ON watch_lifecycle_history "
                         "BEGIN SELECT RAISE(ABORT, 'fixture failure'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.fixture.assertion("relationship", version, self.fixture.now, left_occurrence_id=row,
                                   right_occurrence_id=earlier_rows[0]["id"], status="verified", relation="same_occurrence",
                                   citations=[{"artifact_version_id": item, "locator": "verified original occurrence"}
                                              for item in (version, earlier)])
        pending = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(pending["lifecycleHistory"], admitted["lifecycleHistory"])
        self.assertFalse(pending["currentEvaluation"]["activeEligibility"]["eligible"])
        with self.fixture.connection() as conn:
            conn.execute("DROP TRIGGER fail_watch_history")
        self.fixture.now = ms("2025-08-05T11:17:00-04:00")
        self.assertEqual(self.watch.reevaluate_all(population="test", trigger="startup_recovery"), 1)
        self.assertEqual(self.watch.reevaluate_all(population="test", trigger="startup_recovery"), 0)
        recovered = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(recovered["lifecycleHistory"][-1]["evaluatedAt"], self.fixture.now)
        self.assertEqual(recovered["lifecycleHistory"][-1]["persistedAt"], self.fixture.now)
        self.assertEqual(recovered["lastPersistedAssessment"]["expirySupport"]["expiresAt"], ms("2025-08-02T09:00:00-04:00"))
        self.assertEqual(recovered["lifecycleHistory"][0], admitted["lifecycleHistory"][0])

    def test_later_incompatible_publication_claim_withholds_activity_without_extending_clock(self):
        version, _, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-07-20T10:00:00-04:00")
        self.fixture.assertion("publication", version, self.fixture.now, artifact_version_id=version,
                               precision="exact", raw_value="2025-07-19T09:00:00-04:00")
        result = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertFalse(result["currentEvaluation"]["activeEligibility"]["eligible"])
        self.assertEqual(result["currentEvaluation"]["expirySupport"]["reason"], "publication_evidence_ambiguous")
        self.assertEqual(result["lifecycleHistory"][0]["assessment"]["expirySupport"]["expiresAt"],
                         ms("2025-08-02T09:00:00-04:00"))

    def test_later_publication_narrowing_records_supported_expiry_without_backdating_uncertain_state(self):
        version, rows = self.fixture.official(None)
        self.fixture.assertion("publication", version, ms("2025-07-04T00:00:00-04:00"),
                               artifact_version_id=version, precision="date", raw_value="2025-07-03", timezone="America/New_York")
        self.fixture.identities(version, rows[0]["id"], self.fixture.now)
        admitted = self.watch.admit(f"event:{rows[0]['id']}", population="test")
        self.fixture.now = ms("2025-08-02T08:00:00-04:00")
        self.watch.reevaluate_due(population="test")
        uncertain = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(uncertain["lastPersistedAssessment"]["recency"]["status"], "expiry_uncertain")
        self.fixture.now = ms("2025-08-02T08:15:00-04:00")
        self.fixture.assertion("publication", version, self.fixture.now, artifact_version_id=version,
                               precision="exact", raw_value="2025-07-03T09:00:00-04:00")
        narrowed = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertTrue(narrowed["currentEvaluation"]["activeEligibility"]["eligible"])
        self.assertEqual(narrowed["lifecycleHistory"][-1]["evaluatedAt"], self.fixture.now)
        self.assertEqual(narrowed["currentEvaluation"]["expirySupport"]["expiresAt"], ms("2025-08-02T09:00:00-04:00"))
        self.assertEqual(narrowed["lifecycleHistory"][-2]["assessment"]["recency"]["status"], "expiry_uncertain")

    def test_read_only_current_evaluation_does_not_persist_or_rewrite_history(self):
        _, _, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-08-05T10:00:00-04:00")
        for _ in range(3):
            current = self.watch.get(admitted["watchEvent"]["id"], population="test")
            self.assertEqual(current["lifecycleHistory"], admitted["lifecycleHistory"])
            self.assertEqual(current["currentEvaluation"]["recency"]["status"], "expired")

    def test_corrected_retrospective_cannot_make_later_publication_available_at_original_evaluation(self):
        version, _, event = self.eligible_event(publication=None)
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-07-20T10:00:00-04:00")
        self.fixture.assertion("publication", version, self.fixture.now, artifact_version_id=version,
                               precision="exact", raw_value="2025-07-19T09:00:00-04:00")
        retrospective = self.watch.corrected_retrospective(admitted["lifecycleHistory"][0]["id"],
                                                           population="test", as_of=self.fixture.now)
        self.assertFalse(retrospective["output"]["activeEligibility"]["eligible"])
        self.assertIn("publication_not_available_at_evaluation", retrospective["output"]["lifecycleReasons"])

    def test_conflicting_required_identity_is_unresolved_standing_and_keeps_watch_history(self):
        version, row, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-07-09T10:00:00-04:00")
        self.fixture.assertion("identity", version, self.fixture.now, occurrence_id=row, identity_type="security",
                               identity_id="security:conflict", evidence_type="historical_listing",
                               valid_from="2020-01-01", listing_id="listing:conflict", calendar_id="XNYS")
        result = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertEqual(result["currentEvaluation"]["evidenceStanding"]["status"], "unresolved")
        self.assertEqual(result["currentEvaluation"]["admissionCriteria"]["unresolvedReasons"], ["security_identity_ambiguous"])
        self.assertEqual(result["currentEvaluation"]["admissionCriteria"]["failedReasons"], [])
        self.assertFalse(self.watch.authorize_active_action(admitted["watchEvent"]["id"], population="test")["authorized"])
        self.assertEqual(result["lifecycleHistory"][-1]["transitionReasons"], ["admission_criteria_failed", "standing_unresolved"])

    def test_relationship_split_keeps_original_watch_queryable_and_records_unresolved_criteria(self):
        version, row, event = self.eligible_event()
        self.fixture.disclosures.ingest_supporting_retrieval(RetrievedArtifact(
            population="test", source_name="kadoa", source_url="https://fixture.example/watch-representation",
            media_type="application/json", content=json.dumps([{"ticker": "ABC"}]).encode(),
            retrieved_at_ms=ms("2025-07-04T12:00:00-04:00"), purpose="manual",
            freshness_status="unknown", coverage_status="unknown"))
        retained = self.fixture.disclosures.query_evidence(population="test")
        supporting = next(item["versions"][0] for item in retained["artifacts"] if item["sourceAuthority"] == "supporting")
        citations = [{"artifact_version_id": item, "locator": "explicit correspondence"} for item in (version, supporting["id"])]
        values = dict(left_occurrence_id=row, right_occurrence_id=supporting["rowOccurrences"][0]["id"], citations=citations)
        self.fixture.assertion("relationship", version, self.fixture.now, status="verified", **values)
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-07-09T10:00:00-04:00")
        self.fixture.assertion("relationship", version, self.fixture.now, status="candidate", **values)
        result = self.watch.list(population="test")["watchEvents"][0]
        self.assertEqual(result["watchEvent"]["id"], admitted["watchEvent"]["id"])
        self.assertEqual(result["currentEvaluation"]["evidenceStanding"]["status"], "unresolved")
        self.assertIn("occurrence_counting_ambiguous", result["currentEvaluation"]["admissionCriteria"]["reasons"])
        self.assertFalse(result["currentEvaluation"]["activeEligibility"]["eligible"])
        self.assertEqual(len(result["lifecycleHistory"]), 2)
        self.assertEqual(self.watch.reevaluate_all(population="test", trigger="startup_recovery"), 0)

    def test_merging_already_admitted_occurrences_preserves_history_and_withholds_duplicate_actions(self):
        version, row, event = self.eligible_event()
        first = self.watch.admit(event["id"], population="test")
        other_version, other_rows = self.fixture.official(document="20030002")
        self.fixture.identities(other_version, other_rows[0]["id"], self.fixture.now)
        second = self.watch.admit(f"event:{other_rows[0]['id']}", population="test")
        self.fixture.now = ms("2025-07-09T10:00:00-04:00")
        self.fixture.assertion("relationship", version, self.fixture.now, left_occurrence_id=row,
                               right_occurrence_id=other_rows[0]["id"], status="verified",
                               citations=[{"artifact_version_id": item, "locator": "verified same occurrence"}
                                          for item in (version, other_version)])
        results = self.watch.list(population="test")["watchEvents"]
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertEqual(result["currentEvaluation"]["evidenceStanding"]["status"], "unresolved")
            self.assertIn("admitted_occurrence_identity_conflict", result["currentEvaluation"]["admissionCriteria"]["reasons"])
            self.assertFalse(self.watch.authorize_active_action(result["watchEvent"]["id"], population="test")["authorized"])
        for previous in (first, second):
            self.assertEqual(self.watch.reproduce(previous["lifecycleHistory"][0]["id"], population="test")["output"], previous["lastPersistedAssessment"])

    def test_reinstatement_after_intervening_unresolved_standing_has_distinct_history_reason(self):
        version, row, event = self.eligible_event()
        admitted = self.watch.admit(event["id"], population="test")
        self.fixture.now = ms("2025-07-09T10:00:00-04:00")
        self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row, fields={}, standing="withdrawn")
        self.fixture.now = ms("2025-07-10T10:00:00-04:00")
        self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row, fields={}, standing="unresolved")
        self.fixture.now = ms("2025-07-11T10:00:00-04:00")
        self.fixture.assertion("correction", version, self.fixture.now, occurrence_id=row, fields={}, standing="supported",
                               standing_resolution="reinstatement", citations=self.reinstatement_citations(version))
        result = self.watch.get(admitted["watchEvent"]["id"], population="test")
        self.assertIn("reinstated", result["lifecycleHistory"][-1]["transitionReasons"])
        self.assertTrue(result["currentEvaluation"]["activeEligibility"]["eligible"])


if __name__ == "__main__":
    unittest.main()
