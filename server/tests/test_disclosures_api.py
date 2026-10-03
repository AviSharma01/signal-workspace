import base64
import io
import json
import logging
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from disclosure_sources import FetchedSourceArtifact
from disclosures import DisclosureApplication
from routers import disclosures as disclosure_router


SCHEMA_PATH = Path(__file__).parents[1] / "db" / "schema.sql"


class FakeHouseSource:
    def __init__(self, content: bytes, media_type: str):
        self.content = content
        self.media_type = media_type

    def fetch_index(self, report_year: int) -> FetchedSourceArtifact:
        return FetchedSourceArtifact(
            source_url=(
                "https://disclosures-clerk.house.gov/public_disc/financial-pdfs/"
                f"{report_year}FD.ZIP"
            ),
            media_type=self.media_type,
            content=self.content,
            retrieved_at_ms=1_800_000_000_000,
            http_status=200,
            availability_status="available",
            source_metadata={"etag": '"fixture"'},
        )

    def fetch_filing(self, report_year: int, document_id: str) -> FetchedSourceArtifact:
        return FetchedSourceArtifact(
            source_url=(
                "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/"
                f"{report_year}/{document_id}.pdf"
            ),
            media_type=self.media_type,
            content=self.content,
            retrieved_at_ms=1_800_000_000_000,
            http_status=200,
            availability_status="available",
            source_metadata={"last-modified": "fixture"},
        )


class DisclosureApiTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "signal-api-test.db"
        with self.connection() as conn:
            conn.executescript(SCHEMA_PATH.read_text())
        self.application = DisclosureApplication(self.connection)

        api = FastAPI()
        api.include_router(disclosure_router.router)
        api.dependency_overrides[disclosure_router.get_disclosure_application] = (
            lambda: self.application
        )
        api.dependency_overrides[disclosure_router.get_house_source] = lambda: FakeHouseSource(
            b"%PDF official fixture", "application/pdf"
        )
        self.client = TestClient(api)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    @contextmanager
    def connection(self):
        conn = sqlite3.connect(self.db_path)
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

    def test_supporting_payload_round_trips_through_real_api_without_authority_escalation(self) -> None:
        payload = json.dumps(
            [{"filing_id": "house_20030001", "ticker": " abc "}],
            separators=(",", ":"),
        ).encode()

        created = self.client.post(
            "/api/disclosures/supporting-retrievals",
            json={
                "sourceName": "kadoa",
                "sourceUrl": "https://supporting.example/house.json",
                "mediaType": "application/json",
                "payloadBase64": base64.b64encode(payload).decode(),
                "purpose": "daily_discovery",
                "freshnessStatus": "current",
                "coverageStatus": "partial",
            },
        )

        self.assertEqual(created.status_code, 201, created.text)
        evidence = self.client.get("/api/disclosures/evidence")
        self.assertEqual(evidence.status_code, 200, evidence.text)
        artifact = evidence.json()["artifacts"][0]
        self.assertEqual(artifact["sourceAuthority"], "supporting")
        self.assertEqual(artifact["versions"][0]["rowOccurrences"][0]["rawFields"]["ticker"], " abc ")

        detail = self.client.get(
            f"/api/disclosures/artifacts/{created.json()['artifactId']}"
            f"/versions/{created.json()['artifactVersionId']}"
        )
        self.assertEqual(detail.status_code, 200, detail.text)
        self.assertEqual(base64.b64decode(detail.json()["rawContentBase64"]), payload)

        rejected = self.client.post(
            "/api/disclosures/supporting-retrievals",
            json={
                "sourceName": "house-clerk",
                "sourceUrl": "https://attacker.example/not-official",
                "mediaType": "application/json",
                "payloadBase64": "W10=",
                "purpose": "manual",
                "freshnessStatus": "unknown",
                "coverageStatus": "unknown",
            },
        )
        self.assertEqual(rejected.status_code, 422)

    def test_official_filing_route_constructs_authoritative_source_identity(self) -> None:
        response = self.client.post(
            "/api/disclosures/house/filings/2025/20032062/retrievals",
            json={"purpose": "startup_catch_up"},
        )

        self.assertEqual(response.status_code, 201, response.text)
        evidence = self.client.get("/api/disclosures/evidence").json()
        self.assertEqual(evidence["artifacts"][0]["sourceAuthority"], "official")
        self.assertEqual(evidence["sourceFilings"][0]["sourceFilingId"], "20032062")
        self.assertEqual(
            evidence["artifacts"][0]["retrievalObservations"][0]["purpose"],
            "startup_catch_up",
        )

    def test_official_native_extraction_and_recomputation_are_available_to_api_consumers(self) -> None:
        content = (Path(__file__).parent / "fixtures/house_ptr/2021-20018021.pdf").read_bytes()
        self.client.app.dependency_overrides[disclosure_router.get_house_source] = lambda: FakeHouseSource(content, "application/pdf")
        created = self.client.post(
            "/api/disclosures/house/filings/2021/20018021/retrievals",
            json={"purpose": "manual"},
        )
        self.assertEqual(created.status_code, 201, created.text)
        evidence = self.client.get("/api/disclosures/evidence").json()
        artifact = evidence["artifacts"][0]
        version = artifact["versions"][0]
        row = version["rowOccurrences"][0]
        self.assertEqual(artifact["sourceAuthority"], "official")
        self.assertEqual(row["sourceFiling"]["sourceFilingId"], "20018021")
        self.assertEqual(row["normalizations"][0]["extractionId"], version["extractions"][0]["id"])
        self.assertEqual(row["rawFields"]["sourcePosition"]["page"], 1)
        rerun = self.client.post(
            f"/api/disclosures/artifacts/{artifact['id']}/versions/{version['id']}/extractions",
            json={"extractionMethodVersion": "1", "normalizationMethodVersion": "1"},
        )
        self.assertEqual(rerun.status_code, 200, rerun.text)
        self.assertEqual(rerun.json()["rowOccurrencesCreated"], 0)

    def test_http_error_body_version_is_retained_but_cannot_be_reprocessed_as_a_filing(self) -> None:
        class ErrorBodySource(FakeHouseSource):
            def fetch_filing(self, report_year: int, document_id: str) -> FetchedSourceArtifact:
                fetched = super().fetch_filing(report_year, document_id)
                return FetchedSourceArtifact(
                    source_url=fetched.source_url, media_type="text/html", content=b"<html>Unavailable</html>",
                    retrieved_at_ms=fetched.retrieved_at_ms, http_status=503,
                    availability_status="unavailable", source_metadata={},
                )
        self.client.app.dependency_overrides[disclosure_router.get_house_source] = lambda: ErrorBodySource(b"", "text/html")
        created = self.client.post(
            "/api/disclosures/house/filings/2021/20018021/retrievals", json={"purpose": "manual"},
        )
        self.assertEqual(created.status_code, 201, created.text)
        payload = created.json()
        response = self.client.post(
            f"/api/disclosures/artifacts/{payload['artifactId']}/versions/{payload['artifactVersionId']}/extractions",
            json={"extractionMethodVersion": "1", "normalizationMethodVersion": "1"},
        )
        self.assertEqual(response.status_code, 422, response.text)
        detail = self.client.get(f"/api/disclosures/artifacts/{payload['artifactId']}/versions/{payload['artifactVersionId']}")
        self.assertEqual(base64.b64decode(detail.json()["rawContentBase64"]), b"<html>Unavailable</html>")

    def test_official_api_responses_do_not_expose_unapproved_source_metadata(self) -> None:
        credential_canary = "Bearer " + "sk-" + "runtime-canary-not-a-real-credential-1234567890"

        class MetadataHouseSource(FakeHouseSource):
            def fetch_filing(self, report_year: int, document_id: str) -> FetchedSourceArtifact:
                fetched = super().fetch_filing(report_year, document_id)
                return FetchedSourceArtifact(
                    source_url=fetched.source_url,
                    media_type=fetched.media_type,
                    content=fetched.content,
                    retrieved_at_ms=fetched.retrieved_at_ms,
                    http_status=fetched.http_status,
                    availability_status=fetched.availability_status,
                    source_metadata={
                        "last-modified": "fixture",
                        "authorization": credential_canary,
                    },
                )

        self.client.app.dependency_overrides[disclosure_router.get_house_source] = lambda: (
            MetadataHouseSource(b"%PDF official fixture", "application/pdf")
        )

        log_output = io.StringIO()
        handler = logging.StreamHandler(log_output)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        try:
            created = self.client.post(
                "/api/disclosures/house/filings/2025/20032062/retrievals",
                json={"purpose": "manual"},
            )
            evidence = self.client.get("/api/disclosures/evidence")
        finally:
            root_logger.removeHandler(handler)

        self.assertEqual(created.status_code, 201, created.text)
        self.assertNotIn(credential_canary, created.text)
        self.assertNotIn(credential_canary, evidence.text)
        self.assertNotIn(credential_canary, log_output.getvalue())
        metadata = evidence.json()["artifacts"][0]["retrievalObservations"][0]["sourceMetadata"]
        self.assertEqual(metadata, {"last-modified": "fixture"})

    def test_api_exposes_readiness_without_accepting_fixture_population_selector(self) -> None:
        readiness = self.client.get("/api/disclosures/readiness")
        fixture_query = self.client.get("/api/disclosures/evidence?population=test")

        self.assertEqual(readiness.status_code, 200)
        self.assertEqual(readiness.json()["house"]["availability"], "unavailable")
        self.assertEqual(fixture_query.status_code, 422)

    def test_failed_official_retrieval_is_an_observation_not_an_empty_success(self) -> None:
        class UnavailableHouseSource(FakeHouseSource):
            def fetch_filing(self, report_year: int, document_id: str) -> FetchedSourceArtifact:
                return FetchedSourceArtifact(
                    source_url=(
                        "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/"
                        f"{report_year}/{document_id}.pdf"
                    ),
                    media_type="application/octet-stream",
                    content=None,
                    retrieved_at_ms=1_800_000_000_000,
                    http_status=None,
                    availability_status="unavailable",
                    source_metadata={"errorType": "TimeoutError"},
                )

        self.client.app.dependency_overrides[disclosure_router.get_house_source] = lambda: (
            UnavailableHouseSource(b"", "application/octet-stream")
        )

        response = self.client.post(
            "/api/disclosures/house/filings/2025/20032062/retrievals",
            json={"purpose": "reconciliation"},
        )
        evidence = self.client.get("/api/disclosures/evidence").json()

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["parseStatus"], "not_attempted")
        self.assertEqual(evidence["sourceFilings"], [])
        self.assertEqual(evidence["artifacts"][0]["versions"], [])
        observation = evidence["artifacts"][0]["retrievalObservations"][0]
        self.assertEqual(observation["availabilityStatus"], "unavailable")
        self.assertEqual(observation["freshnessStatus"], "unknown")
        self.assertEqual(observation["coverageStatus"], "unknown")
        self.assertEqual(observation["sourceMetadata"], {"errorType": "TimeoutError"})

    def test_official_retrieval_rejects_invalid_locators_at_the_api_boundary(self) -> None:
        invalid_year = self.client.post(
            "/api/disclosures/house/indexes/1900/retrievals",
            json={"purpose": "manual"},
        )
        invalid_document = self.client.post(
            "/api/disclosures/house/filings/2025/not-a-document/retrievals",
            json={"purpose": "manual"},
        )

        self.assertEqual(invalid_year.status_code, 422)
        self.assertEqual(invalid_document.status_code, 422)

    def test_versioned_reprocessing_is_exposed_through_the_api(self) -> None:
        created = self.client.post(
            "/api/disclosures/supporting-retrievals",
            json={
                "sourceName": "kadoa",
                "sourceUrl": "https://supporting.example/reprocess.json",
                "mediaType": "application/json",
                "payloadBase64": base64.b64encode(b'[{"ticker":" abc "}]').decode(),
                "purpose": "manual",
                "freshnessStatus": "unknown",
                "coverageStatus": "unknown",
            },
        ).json()

        recomputed = self.client.post(
            f"/api/disclosures/artifacts/{created['artifactId']}"
            f"/versions/{created['artifactVersionId']}/extractions",
            json={"extractionMethodVersion": "2", "normalizationMethodVersion": "2"},
        )
        evidence = self.client.get("/api/disclosures/evidence").json()

        self.assertEqual(recomputed.status_code, 200, recomputed.text)
        version = evidence["artifacts"][0]["versions"][0]
        self.assertEqual(len(version["rowOccurrences"]), 1)
        self.assertEqual(version["extractions"][1]["representation"]["container"], "list")


if __name__ == "__main__":
    unittest.main()
