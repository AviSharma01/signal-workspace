import json
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import events
from routers import events as event_router
from tests import test_events
from tests.test_events import ms


class EventApiTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_events.EventApplicationTest()
        self.fixture.setUp()
        api = FastAPI()
        api.include_router(event_router.router)
        api.dependency_overrides[event_router.get_event_application] = lambda: self.fixture.events
        self.client = TestClient(api)

    def tearDown(self):
        self.client.close()
        self.fixture.tearDown()

    def get_view(self):
        return self.client.get("/api/events", params={
            "perspective": "public_information", "asOf": ms("2025-07-08T20:00:00-04:00")})

    def test_empty_event_result_does_not_mean_event_derivation_is_unavailable(self):
        view = self.get_view().json()

        self.assertEqual(view["capability"]["availability"], "available")
        self.assertEqual(view["result"]["state"], "empty")
        self.assertEqual(view["events"], [])

    def test_api_exposes_event_evidence_eligibility_and_coverage_with_camel_case_record_keys(self):
        # Physically isolated test DB: only this test's designated real population.
        self.fixture.population = "real"
        version, rows = self.fixture.official()
        self.fixture.identities(version, rows[0]["id"], ms("2025-07-03T09:00:00-04:00"))
        self.fixture.calendar(version, ms("2025-07-03T09:00:00-04:00"))
        response = self.get_view()
        self.assertEqual(response.status_code, 200, response.text)
        view = response.json()
        event = view["events"][0]
        self.assertTrue(event["eligibility"]["primaryAnalysis"]["eligible"])
        self.assertEqual(event["anchor"]["openAt"], ms("2025-07-03T09:30:00-04:00"))
        self.assertIn("transaction_type", event["provenance"]["rows"][0]["rawFields"])
        self.assertEqual(event["identities"]["security"]["identity"]["identityId"], "security:ABC")
        self.assertEqual(view["coverage"]["readiness"]["house"]["availability"], "unavailable")
        self.assertEqual(view["marketOutcomes"]["availability"], "unavailable")
        self.assertEqual(view["marketOutcomes"]["capability"]["availability"], "unavailable")
        self.assertEqual(view["marketOutcomes"]["result"]["state"], "empty")
        self.assertEqual(view["marketOutcomes"]["outcomes"], [])

    def test_api_rejects_fixture_population_and_cross_population_citations(self):
        version, _ = self.fixture.official()
        self.assertEqual(self.get_view().json()["events"], [])
        self.assertEqual(self.client.get("/api/events", params={"perspective": "public_information", "asOf": self.fixture.now,
                                                              "population": "test"}).status_code, 422)
        rejected = self.client.post("/api/events/evidence-assertions", json={
            "kind": "publication", "citations": [{"artifactVersionId": version, "locator": "row"}],
            "publicAt": ms("2025-07-03T09:00:00-04:00"), "basis": "fixture", "artifactVersionId": version,
            "precision": "exact", "rawValue": "2025-07-03T09:00:00-04:00"})
        self.assertEqual(rejected.status_code, 422, rejected.text)

    def test_api_records_immutable_views_and_labels_corrected_retrospective_boundary(self):
        self.fixture.population = "real"
        version, rows = self.fixture.official()
        request = {"perspective": "public_information", "asOf": ms("2025-07-03T10:00:00-04:00")}
        created = self.client.post("/api/events/views", json=request)
        self.assertEqual(created.status_code, 201, created.text)
        recorded = created.json()
        self.assertEqual(recorded["capability"]["availability"], "available")
        self.assertEqual(recorded["marketOutcomes"]["capability"]["availability"], "unavailable")
        correction = self.client.post("/api/events/evidence-assertions", json={
            "kind": "correction", "citations": [{"artifactVersionId": version, "locator": "field correction"}],
            "publicAt": ms("2025-07-07T10:00:00-04:00"), "basis": "official correction to direction only",
            "occurrenceId": rows[0]["id"], "fields": {"transactionDirection": "sale"}})
        self.assertEqual(correction.status_code, 201, correction.text)
        retrieved = self.client.get(f"/api/events/views/{recorded['id']}")
        self.assertEqual(retrieved.json(), recorded)
        reproduced = self.client.get(f"/api/events/views/{recorded['id']}/reproduction")
        self.assertEqual(reproduced.status_code, 200, reproduced.text)
        self.assertEqual(reproduced.json()["recordType"], "deterministic_reproduction")
        self.assertEqual(reproduced.json()["output"], recorded)
        corrected = self.client.post("/api/events/views", json={
            "perspective": "public_information", "asOf": self.fixture.now,
            "mode": "corrected_retrospective", "originalAsOf": request["asOf"]})
        self.assertEqual(corrected.status_code, 201, corrected.text)
        self.assertEqual(corrected.json()["events"][0]["fields"]["transactionDirection"], "sale")
        self.assertEqual(corrected.json()["events"][0]["fields"]["transactionDate"], "2025-07-01")
        self.assertEqual(corrected.json()["events"][0]["fields"]["amountLower"], 1001)
        self.assertEqual(corrected.json()["events"][0]["fields"]["amountUpper"], 15000)
        self.assertEqual(corrected.json()["events"][0]["intrinsicState"]["fields"]["transactionDirection"], "purchase")
        self.assertEqual(corrected.json()["mode"], "corrected_retrospective")
        self.assertEqual(corrected.json()["recordType"], "recorded_output")
        invalid = self.client.post("/api/events/views", json={**request, "mode": "corrected_retrospective"})
        self.assertEqual(invalid.status_code, 422)

    def test_api_rejects_fabricated_exact_precision_unknown_zones_and_future_asof(self):
        self.fixture.population = "real"
        version, _ = self.fixture.official(None)
        command = {"kind": "publication", "citations": [{"artifactVersionId": version, "locator": "publication statement"}],
                   "publicAt": ms("2025-07-03T09:00:00-04:00"), "basis": "fixture", "artifactVersionId": version,
                   "precision": "exact", "rawValue": "2025-07-03T09:00:00"}
        self.assertEqual(self.client.post("/api/events/evidence-assertions", json=command).status_code, 422)
        invalid_zone = {**command, "precision": "date", "rawValue": "2025-07-03", "timezone": "Unresolved/Zone"}
        self.assertEqual(self.client.post("/api/events/evidence-assertions", json=invalid_zone).status_code, 422)
        self.assertEqual(self.client.get("/api/events", params={"perspective": "public_information", "asOf": self.fixture.now + 1}).status_code, 422)
        self.assertEqual(self.client.get("/api/events/views/missing").status_code, 404)

    def test_assertion_method_provenance_is_persisted_read_and_reproduced_unchanged(self):
        self.fixture.population = "real"
        version, rows = self.fixture.official(None)
        shared = {"citations": [{"artifactVersionId": version, "locator": "official evidence"}],
                  "publicAt": ms("2025-07-03T09:00:00-04:00"), "basis": "retained evidence"}
        commands = [
            {**shared, "kind": "publication", "artifactVersionId": version,
             "precision": "exact", "rawValue": "2025-07-03T09:00:00-04:00"},
            {**shared, "kind": "identity", "occurrenceId": rows[0]["id"],
             "identityType": "member", "identityId": "member:verified",
             "evidenceType": "stable_source_identifier", "validFrom": "2025-01-01"},
        ]
        assertions = []
        for command in commands:
            created = self.client.post("/api/events/evidence-assertions", json=command)
            self.assertEqual(created.status_code, 201, created.text)
            assertion = created.json()
            self.assertEqual(assertion["methodVersion"], "event-pit@1")
            assertions.append(assertion)
            with self.fixture.connection() as conn:
                persisted = json.loads(conn.execute(
                    "SELECT assertion_json FROM event_evidence_assertions WHERE id = ?",
                    (assertion["id"],)).fetchone()["assertion_json"])
            self.assertEqual(persisted["method_version"], assertion["methodVersion"])

        view = self.get_view()
        self.assertEqual(view.status_code, 200, view.text)
        event = view.json()["events"][0]
        self.assertEqual(event["publication"]["evidence"][0]["methodVersion"], "event-pit@1")
        self.assertEqual(event["identities"]["member"]["identity"]["methodVersion"], "event-pit@1")
        created = self.client.post("/api/events/views", json={
            "perspective": "public_information", "asOf": self.fixture.now})
        self.assertEqual(created.status_code, 201, created.text)
        recorded = created.json()
        url = f"/api/events/views/{recorded['id']}"
        reproduced = self.client.get(f"{url}/reproduction")
        self.assertEqual(reproduced.status_code, 200, reproduced.text)
        self.assertEqual(reproduced.json()["output"], recorded)

        with patch.object(events, "METHOD_VERSION", "event-pit@2"):
            self.assertEqual(self.client.get(url).json(), recorded)
            rejected = self.client.get(f"{url}/reproduction")
            self.assertEqual(rejected.status_code, 422, rejected.text)
            self.assertIn("recorded method version", rejected.json()["detail"])
            rejected = self.get_view()
            self.assertEqual(rejected.status_code, 422, rejected.text)
            self.assertIn("unsupported assertion method version", rejected.json()["detail"])
            with self.fixture.connection() as conn:
                for assertion in assertions:
                    persisted = json.loads(conn.execute(
                        "SELECT assertion_json FROM event_evidence_assertions WHERE id = ?",
                        (assertion["id"],)).fetchone()["assertion_json"])
                    self.assertEqual(persisted["method_version"], "event-pit@1")

    def test_recorded_amount_conflict_is_reproduced_and_only_later_eligible_evidence_resolves_it(self):
        self.fixture.population = "real"
        self.fixture.now = ms("2025-07-03T12:00:00-04:00")
        version, rows = self.fixture.official()
        self.fixture.identities(version, rows[0]["id"], ms("2025-07-03T09:00:00-04:00"))
        self.fixture.calendar(version, ms("2025-07-03T09:00:00-04:00"))
        self.fixture.now = ms("2025-07-07T11:00:00-04:00")
        command = {"kind": "correction", "citations": [{"artifactVersionId": version, "locator": "amount correction"}],
                   "publicAt": ms("2025-07-07T10:00:00-04:00"), "basis": "official lower-bound correction",
                   "occurrenceId": rows[0]["id"], "fields": {"amountLower": 20000}}
        correction = self.client.post("/api/events/evidence-assertions", json=command)
        self.assertEqual(correction.status_code, 201, correction.text)
        self.assertEqual(correction.json()["fields"], {"amount_lower": 20000})
        created = self.client.post("/api/events/views", json={
            "perspective": "system_observation", "asOf": self.fixture.now})
        self.assertEqual(created.status_code, 201, created.text)
        recorded = created.json()
        event = recorded["events"][0]
        conflict = {"eligible": False, "reasons": ["amount_range_conflict"]}
        self.assertEqual(event["eligibility"]["amountFeatures"], conflict)
        self.assertEqual((event["fields"]["amountLower"], event["fields"]["amountUpper"]), (20000, 15000))
        self.assertEqual(event["provenance"]["rows"][0]["rawFields"]["amount"], "$1,001 - $15,000")
        self.assertTrue(event["eligibility"]["watchAdmissionPrerequisites"]["eligible"])
        url = f"/api/events/views/{recorded['id']}"
        reproduced = self.client.get(f"{url}/reproduction")
        self.assertEqual(reproduced.status_code, 200, reproduced.text)
        self.assertEqual(reproduced.json()["output"], recorded)

        self.fixture.now = ms("2025-07-08T20:00:00-04:00")
        resolution = self.client.post("/api/events/evidence-assertions", json={
            **command, "publicAt": ms("2025-07-08T10:00:00-04:00"),
            "basis": "later official upper-bound correction", "fields": {"amountUpper": 30000}})
        self.assertEqual(resolution.status_code, 201, resolution.text)
        self.assertEqual(resolution.json()["fields"], {"amount_upper": 30000})
        for as_of, bounds, eligibility in [
            (recorded["asOf"], (20000, 15000), conflict),
            (self.fixture.now, (20000, 30000), {"eligible": True, "reasons": []}),
        ]:
            corrected = self.client.post("/api/events/views", json={
                "perspective": "public_information", "asOf": as_of,
                "mode": "corrected_retrospective", "originalAsOf": ms("2025-07-03T13:00:00-04:00")})
            self.assertEqual(corrected.status_code, 201, corrected.text)
            event = corrected.json()["events"][0]
            self.assertEqual((event["fields"]["amountLower"], event["fields"]["amountUpper"]), bounds)
            self.assertEqual(event["eligibility"]["amountFeatures"], eligibility)
            self.assertEqual(event["intrinsicState"]["fields"]["amountLower"], 1001)
        self.assertEqual(self.client.get(url).json(), recorded)
        reproduced = self.client.get(f"{url}/reproduction")
        self.assertEqual(reproduced.status_code, 200, reproduced.text)
        self.assertEqual(reproduced.json()["output"], recorded)

    def test_reproduction_rejects_missing_or_unsupported_assertion_method_provenance(self):
        self.fixture.population = "real"
        self.fixture.official()
        created = self.client.post("/api/events/views", json={
            "perspective": "public_information", "asOf": self.fixture.now})
        self.assertEqual(created.status_code, 201, created.text)
        recorded = created.json()
        with self.fixture.connection() as conn:
            row = conn.execute("SELECT id, assertion_json FROM event_evidence_assertions").fetchone()
        original = json.loads(row["assertion_json"])
        for method_version, reason in [(None, "missing assertion method version"),
                                       ("event-pit@999", "unsupported assertion method version")]:
            with self.subTest(method_version=method_version):
                legacy = dict(original)
                if method_version is None:
                    legacy.pop("method_version", None)
                else:
                    legacy["method_version"] = method_version
                # Only simulate legacy/unsupported storage in this isolated fixture DB.
                with self.fixture.connection() as conn:
                    conn.execute("UPDATE event_evidence_assertions SET assertion_json = ? WHERE id = ?",
                                 (json.dumps(legacy), row["id"]))
                for response in [self.get_view(), self.client.get(
                        f"/api/events/views/{recorded['id']}/reproduction")]:
                    self.assertEqual(response.status_code, 422, response.text)
                    self.assertIn(reason, response.json()["detail"])
                self.assertEqual(self.client.get(f"/api/events/views/{recorded['id']}").json(), recorded)


if __name__ == "__main__":
    unittest.main()
