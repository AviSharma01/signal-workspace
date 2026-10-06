import json
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers import findings, prices, scan


SCHEMA_PATH = Path(__file__).parents[1] / "db" / "schema.sql"


class V1CapabilityContainmentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "containment.db"
        with self.connection() as conn:
            conn.executescript(SCHEMA_PATH.read_text())
            conn.execute("INSERT INTO companies (id, name, sector) VALUES ('TEST', 'Test', 'Test')")
            conn.execute(
                "INSERT INTO price_points (company_id, timestamp, open, high, low, close, volume) "
                "VALUES ('TEST', 4102444800000, 10, 11, 9, 10.5, 1000)"
            )
            conn.execute(
                "INSERT INTO findings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    "legacy-finding",
                    "TEST",
                    1,
                    json.dumps({"z_score": 4}),
                    "news",
                    "legacy hypothesis",
                    "[]",
                    "high",
                    0,
                    1,
                    0.0,
                ),
            )

        api = FastAPI()
        api.include_router(prices.router)
        api.include_router(findings.router)
        api.include_router(scan.router)
        api.dependency_overrides[prices.get_connection] = lambda: self.connection()
        self.client = TestClient(api)

    def tearDown(self) -> None:
        self.client.close()
        self.temp_dir.cleanup()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def test_seeded_price_rows_are_not_a_v2_market_result(self) -> None:
        response = self.client.get("/api/prices/TEST", params={"range": "1D"})

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["capability"]["availability"], "unavailable")
        self.assertEqual(payload["result"]["state"], "empty")
        self.assertEqual(payload["prices"], [])
        self.assertTrue(payload["legacyDataExcluded"])

    def test_legacy_findings_are_not_v2_investigation_results(self) -> None:
        response = self.client.get("/api/findings", params={"ticker": "TEST"})

        self.assertEqual(response.status_code, 200, response.text)
        payload = response.json()
        self.assertEqual(payload["capability"]["availability"], "unavailable")
        self.assertEqual(payload["result"]["state"], "empty")
        self.assertEqual(payload["findings"], [])
        self.assertTrue(payload["legacyDataExcluded"])

    def test_legacy_scan_action_is_rejected_with_capability_and_request_state(self) -> None:
        response = self.client.post("/api/scan/run")

        self.assertEqual(response.status_code, 409, response.text)
        payload = response.json()
        self.assertEqual(payload["capability"]["availability"], "unavailable")
        self.assertEqual(payload["result"]["state"], "error")
        self.assertIn("legacy_v1_scan_disabled", payload["capability"]["reasonCodes"])


if __name__ == "__main__":
    unittest.main()
