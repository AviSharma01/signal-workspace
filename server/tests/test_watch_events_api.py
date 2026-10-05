import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import watch_events
from routers import events as event_router, watch_events as watch_router
from tests import test_events
from watch_events import WatchApplication


ms = test_events.ms


class WatchApiTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_events.EventApplicationTest()
        self.fixture.setUp()
        self.fixture.population = "real"
        self.watch = WatchApplication(self.fixture.connection, lambda: self.fixture.now)
        api = FastAPI()
        api.include_router(event_router.router)
        api.include_router(watch_router.router)
        api.dependency_overrides[event_router.get_event_application] = lambda: self.fixture.events
        api.dependency_overrides[watch_router.get_watch_application] = lambda: self.watch
        self.client = TestClient(api)

    def tearDown(self):
        self.client.close()
        self.fixture.tearDown()

    def admit(self, *, document="20030001", publication="2025-07-03T09:00:00-04:00"):
        version, rows = self.fixture.official(publication, document=document)
        self.fixture.identities(version, rows[0]["id"], self.fixture.now)
        response = self.client.post("/api/watch-events/admissions", json={"eventId": f"event:{rows[0]['id']}"})
        self.assertEqual(response.status_code, 201, response.text)
        return version, rows[0]["id"], response.json()

    def test_api_admits_and_exposes_current_persisted_and_history_separately(self):
        _, _, result = self.admit()
        watch_id = result["watchEvent"]["id"]
        self.assertEqual(result["currentEvaluation"]["recency"]["status"], "within_window")
        self.assertEqual(result["lifecycleHistory"][0]["recordType"], "recorded_historical_state")
        self.assertEqual(result["currentEvent"]["identities"]["member"]["identity"]["identityId"], "member:001")
        self.assertEqual(self.client.get(f"/api/watch-events/{watch_id}").json(), result)
        self.assertEqual(len(self.client.get("/api/watch-events").json()["watchEvents"]), 1)

        self.fixture.now = ms("2025-08-02T09:00:00-04:00")
        current = self.client.get(f"/api/watch-events/{watch_id}").json()
        self.assertTrue(current["lastPersistedAssessment"]["activeEligibility"]["eligible"])
        self.assertFalse(current["currentEvaluation"]["activeEligibility"]["eligible"])
        self.assertTrue(current["currentDiffersFromLastPersisted"])
        action = self.client.post(f"/api/watch-events/{watch_id}/active-eligibility")
        self.assertEqual(action.status_code, 200, action.text)
        self.assertFalse(action.json()["authorized"])
        self.assertEqual(len(self.client.get(f"/api/watch-events/{watch_id}").json()["lifecycleHistory"]), 2)

    def test_evidence_api_reevaluates_withdrawal_and_requires_explicit_reinstatement(self):
        version, row, result = self.admit()
        url = f"/api/watch-events/{result['watchEvent']['id']}"
        self.fixture.now = ms("2025-07-09T10:00:00-04:00")
        command = {"kind": "correction", "occurrenceId": row, "fields": {}, "standing": "withdrawn",
                   "citations": [{"artifactVersionId": version, "locator": "official withdrawal"}],
                   "publicAt": self.fixture.now, "basis": "official cancellation"}
        response = self.client.post("/api/events/evidence-assertions", json=command)
        self.assertEqual(response.status_code, 201, response.text)
        withdrawn = self.client.get(url).json()
        self.assertEqual(withdrawn["lastPersistedAssessment"]["evidenceStanding"]["status"], "withdrawn")
        self.fixture.now += 1000
        unchanged = self.client.post("/api/events/evidence-assertions", json={**command, "standing": "supported"})
        self.assertEqual(unchanged.status_code, 201, unchanged.text)
        self.assertEqual(self.client.get(url).json()["currentEvaluation"]["evidenceStanding"]["status"], "withdrawn")
        self.fixture.now += 1000
        unchanged = self.client.post("/api/events/evidence-assertions", json={
            **command, "standing": "supported", "standingResolution": "reinstatement"})
        self.assertEqual(unchanged.status_code, 201, unchanged.text)
        self.assertEqual(self.client.get(url).json()["currentEvaluation"]["evidenceStanding"]["status"], "withdrawn")
        new_version, _ = self.fixture.official(None, document="20030009", observed=self.fixture.now,
                                              asset="Explicit reinstatement evidence (ABC) [ST]")
        reinstated = self.client.post("/api/events/evidence-assertions", json={
            **command, "standing": "supported", "standingResolution": "reinstatement",
            "citations": [{"artifactVersionId": item, "locator": "official reinstatement statement"} for item in (version, new_version)],
            "basis": "new official statement explicitly reinstates occurrence"})
        self.assertEqual(reinstated.status_code, 201, reinstated.text)
        restored = self.client.get(url).json()
        self.assertTrue(restored["currentEvaluation"]["activeEligibility"]["eligible"])
        self.assertEqual(restored["lifecycleHistory"][-1]["transitionReasons"], ["reinstated"])

    def test_replay_api_keeps_recorded_reproduction_and_later_views_distinct(self):
        version, _, result = self.admit(publication=None)
        watch_id = result["watchEvent"]["id"]
        history_id = result["lifecycleHistory"][0]["id"]
        base = f"/api/watch-events/{watch_id}/assessments/{history_id}"
        self.fixture.now = ms("2025-07-09T10:00:00-04:00")
        self.fixture.assertion("publication", version, ms("2025-07-03T09:00:00-04:00"), artifact_version_id=version,
                               precision="exact", raw_value="2025-07-03T09:00:00-04:00")
        self.assertEqual(self.client.get(base).json()["assessment"]["recency"]["status"], "publication_age_unknown")
        for mode in ("reproduction", "recomputation"):
            response = self.client.get(f"{base}/{mode}")
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["output"]["recency"]["status"], "publication_age_unknown")
        corrected = self.client.get(f"{base}/corrected-retrospective", params={"asOf": self.fixture.now})
        self.assertEqual(corrected.status_code, 200, corrected.text)
        self.assertEqual(corrected.json()["output"]["recency"]["status"], "within_window")
        self.assertEqual(corrected.json()["recordType"], "corrected_retrospective")

        with patch.object(watch_events, "POLICY_VERSION", "watch-lifecycle@999"):
            self.assertEqual(self.client.get(base).status_code, 200)
            self.assertEqual(self.client.get(f"{base}/reproduction").status_code, 422)

    def test_assessment_paths_are_bound_to_watch_and_fixture_populations_cannot_be_admitted(self):
        _, _, first = self.admit()
        _, _, second = self.admit(document="20030002")
        assessment_id = first["lifecycleHistory"][0]["id"]
        for suffix in ("", "/reproduction", "/recomputation", "/corrected-retrospective?asOf=1"):
            response = self.client.get(f"/api/watch-events/{second['watchEvent']['id']}/assessments/{assessment_id}{suffix}")
            self.assertEqual(response.status_code, 404, response.text)
        self.fixture.population = "test"
        version, rows = self.fixture.official(document="20030003")
        self.fixture.identities(version, rows[0]["id"], self.fixture.now)
        response = self.client.post("/api/watch-events/admissions", json={"eventId": f"event:{rows[0]['id']}"})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.post("/api/watch-events/admissions", json={
            "eventId": first["watchEvent"]["eventId"], "population": "test", "admittedAt": 1}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
