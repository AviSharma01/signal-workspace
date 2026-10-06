import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from capabilities import CapabilityApplication
from routers import capabilities as capability_router


class CapabilityApiTest(unittest.TestCase):
    def setUp(self) -> None:
        api = FastAPI()
        api.include_router(capability_router.router)
        self.client = TestClient(api)

    def tearDown(self) -> None:
        self.client.close()

    def test_catalog_exposes_availability_separately_from_result(self) -> None:
        response = self.client.get("/api/capabilities")

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["contractVersion"], "signal-capabilities@1")
        self.assertEqual(payload["result"]["state"], "successful")
        capabilities = {item["id"]: item for item in payload["capabilities"]}
        self.assertEqual(
            {item["availability"] for item in capabilities.values()},
            {"available", "unavailable"},
        )
        for capability in capabilities.values():
            self.assertIsInstance(capability["reasonCodes"], list)
            self.assertIsInstance(capability["detail"], str)
            self.assertIsInstance(capability["evaluatedAt"], int)
            self.assertIsInstance(capability["governingVersion"], str)
            self.assertIsInstance(capability["unmetPrerequisites"], list)

    def test_market_consensus_and_investigation_boundaries_are_explicit(self) -> None:
        payload = self.client.get("/api/capabilities").json()
        capabilities = {item["id"]: item for item in payload["capabilities"]}

        for capability_id in (
            "analysis.market_event_study",
            "market.outcomes",
            "monitoring.market_checks",
            "monitoring.market_anomaly_detection",
            "investigation.market_triggered",
        ):
            capability = capabilities[capability_id]
            self.assertEqual(capability["availability"], "unavailable")
            self.assertIn("market_data_contract_unsatisfied", capability["reasonCodes"])
            self.assertGreaterEqual(len(capability["unmetPrerequisites"]), 2)

        for capability_id in (
            "analysis.consensus.raw",
            "analysis.consensus.expected",
            "analysis.consensus.excess",
        ):
            capability = capabilities[capability_id]
            self.assertEqual(capability["availability"], "unavailable")
            self.assertIn("consensus_deferred_unsupported_evidence", capability["reasonCodes"])
            for forbidden_result_field in ("value", "count", "score", "result"):
                self.assertNotIn(forbidden_result_field, capability)

        evaluation = capabilities["investigation.selection_evaluation"]
        self.assertEqual(evaluation["availability"], "unavailable")
        self.assertIn("independent_evaluation_target_unavailable", evaluation["reasonCodes"])
        self.assertEqual(
            capabilities["monitoring.market_anomaly_detection"]["reasonCodes"],
            ["market_data_contract_unsatisfied", "market_anomaly_thresholds_not_approved"],
        )
        self.assertEqual(
            capabilities["investigation.market_triggered"]["reasonCodes"],
            ["market_data_contract_unsatisfied", "market_investigation_trigger_criteria_not_approved"],
        )

    def test_watch_lifecycle_is_available_while_current_discovery_readiness_is_unavailable(self) -> None:
        payload = self.client.get("/api/capabilities").json()
        capabilities = {item["id"]: item for item in payload["capabilities"]}

        self.assertEqual(capabilities["events.derivation"]["availability"], "available")
        self.assertEqual(capabilities["monitoring.watch_lifecycle"]["availability"], "available")
        self.assertEqual(capabilities["monitoring.disclosure_discovery"]["availability"], "unavailable")
        self.assertIn(
            "chamber_readiness_unavailable",
            capabilities["monitoring.disclosure_discovery"]["reasonCodes"],
        )
        self.assertEqual(capabilities["analysis.market_event_study"]["availability"], "unavailable")

    def test_partial_chamber_readiness_cannot_activate_dependent_capabilities(self) -> None:
        def readiness():
            def chamber(name: str, availability: str) -> dict:
                return {
                    "chamber": name,
                    "availability": availability,
                    "reason_codes": ["fixture_gate"],
                    "detail": "Fixture readiness gate.",
                    "evaluated_at": 10,
                    "governing_version": "fixture@1",
                    "unmet_prerequisites": [{"code": "gate", "detail": "gate"}],
                }

            return {
                "house": chamber("house", "conditional"),
                "senate": chamber("senate", "unavailable"),
            }

        self.client.app.dependency_overrides[
            capability_router.get_capability_application
        ] = lambda: CapabilityApplication(readiness, clock=lambda: 20)
        payload = self.client.get("/api/capabilities").json()
        capabilities = {item["id"]: item for item in payload["capabilities"]}

        self.assertEqual(capabilities["disclosure.house"]["availability"], "conditional")
        self.assertEqual(capabilities["analysis.disclosure_coverage"]["availability"], "conditional")
        self.assertEqual(capabilities["monitoring.disclosure_discovery"]["availability"], "conditional")
        self.assertEqual(capabilities["analysis.market_event_study"]["availability"], "unavailable")
        self.assertEqual(capabilities["monitoring.market_checks"]["availability"], "unavailable")

    def test_contract_contains_no_provider_payload_or_secret_shaped_fields(self) -> None:
        response_text = self.client.get("/api/capabilities").text.lower()
        for forbidden in ("authorization", "api_key", "access_token", "provider_response"):
            self.assertNotIn(forbidden, response_text)

class MarketReadinessApiTest(unittest.TestCase):
    def test_catalog_exposes_exact_production_gates_after_synthetic_evaluation(self):
        from market_fixture import fixture, SyntheticAdapter
        from market_conformance import MarketConformanceApplication
        scope, evidence = fixture()
        self.assertEqual(MarketConformanceApplication().evaluate(scope, evidence, adapter=SyntheticAdapter())['readiness']['availability'], 'available')
        api = FastAPI()
        api.include_router(capability_router.router)
        with TestClient(api) as client:
            payload = client.get('/api/capabilities').json()
        capabilities = {item['id']: item for item in payload['capabilities']}
        readiness = capabilities['market.data_readiness']
        self.assertEqual(readiness['evaluationScope'], 'production')
        self.assertEqual(readiness['availability'], 'unavailable')
        codes = {item['code'] for item in readiness['unmetPrerequisites']}
        self.assertIn('split_handling', codes)
        self.assertIn('explicit_provider_approval', codes)
        self.assertTrue(all(item['status'] == 'unsupported' for item in readiness['unmetPrerequisites']))
        for key in ('analysis.market_event_study', 'market.outcomes', 'monitoring.market_checks', 'monitoring.market_anomaly_detection', 'investigation.market_triggered'):
            self.assertEqual(capabilities[key]['availability'], 'unavailable')
            self.assertTrue(codes.issubset({item['code'] for item in capabilities[key]['unmetPrerequisites']}))
            self.assertNotIn('result', capabilities[key])


if __name__ == "__main__":
    unittest.main()
