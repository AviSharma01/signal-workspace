import json
import sqlite3
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

from disclosures import DisclosureApplication, RetrievedArtifact


SCHEMA_PATH = Path(__file__).parents[1] / "db" / "schema.sql"


class DisclosureApplicationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "signal-test.db"
        with self.connection() as conn:
            conn.executescript(SCHEMA_PATH.read_text())
        self.application = DisclosureApplication(self.connection)

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

    def test_unchanged_retrieval_adds_observation_without_duplicate_version_or_rows(self) -> None:
        payload = json.dumps(
            [
                {"filing_id": "house_20030001", "ticker": "ABC", "amount": "$1,001 - $15,000"},
                {"filing_id": "house_20030001", "ticker": "ABC", "amount": "$1,001 - $15,000"},
            ],
            separators=(",", ":"),
        ).encode()

        first = self.application.ingest_supporting_retrieval(
            RetrievedArtifact(
                population="test",
                source_name="kadoa",
                source_url="https://supporting.example/house.json",
                media_type="application/json",
                content=payload,
                retrieved_at_ms=1_800_000_000_000,
                purpose="daily_discovery",
                freshness_status="current",
                coverage_status="partial",
            )
        )
        second = self.application.ingest_supporting_retrieval(
            RetrievedArtifact(
                population="test",
                source_name="kadoa",
                source_url="https://supporting.example/house.json",
                media_type="application/json",
                content=payload,
                retrieved_at_ms=1_800_000_060_000,
                purpose="startup_catch_up",
                freshness_status="current",
                coverage_status="partial",
            )
        )

        evidence = self.application.query_evidence(population="test")

        self.assertTrue(first["versionCreated"])
        self.assertFalse(second["versionCreated"])
        self.assertEqual(len(evidence["artifacts"]), 1)
        self.assertEqual(len(evidence["artifacts"][0]["versions"]), 1)
        self.assertEqual(len(evidence["artifacts"][0]["retrievalObservations"]), 2)
        self.assertEqual(len(evidence["artifacts"][0]["versions"][0]["rowOccurrences"]), 2)
        self.assertNotEqual(
            evidence["artifacts"][0]["versions"][0]["rowOccurrences"][0]["id"],
            evidence["artifacts"][0]["versions"][0]["rowOccurrences"][1]["id"],
        )

    def test_changed_content_creates_a_version_without_amendment_or_row_correspondence_claims(self) -> None:
        initial = json.dumps(
            [{"filing_id": "house_20030001", "ticker": "ABC"}],
            separators=(",", ":"),
        ).encode()
        changed = json.dumps(
            [{"filing_id": "house_20030001", "ticker": "XYZ"}],
            separators=(",", ":"),
        ).encode()

        first = self._ingest_supporting(initial, retrieved_at_ms=1_800_000_000_000)
        second = self._ingest_supporting(changed, retrieved_at_ms=1_800_000_060_000)
        evidence = self.application.query_evidence(population="test")

        self.assertTrue(first["versionCreated"])
        self.assertTrue(second["versionCreated"])
        versions = evidence["artifacts"][0]["versions"]
        self.assertEqual(len(versions), 2)
        self.assertEqual([len(version["rowOccurrences"]) for version in versions], [1, 1])
        self.assertNotIn("amendment", evidence["artifacts"][0])
        self.assertNotIn("correspondence", versions[1]["rowOccurrences"][0])

    def test_malformed_payload_retains_raw_bytes_and_independent_statuses(self) -> None:
        malformed = b'{"trades":[{"ticker":"ABC"}'
        result = self._ingest_supporting(
            malformed,
            retrieved_at_ms=1_800_000_000_000,
            freshness_status="stale",
            coverage_status="unknown",
        )

        detail = self.application.get_artifact_version(
            result["artifactId"],
            result["artifactVersionId"],
            population="test",
        )

        self.assertEqual(result["parseStatus"], "failed")
        self.assertEqual(detail["rawContent"], malformed)
        self.assertEqual(detail["extractions"][0]["status"], "failed")
        self.assertEqual(detail["retrievalObservations"][0]["availabilityStatus"], "available")
        self.assertEqual(detail["retrievalObservations"][0]["freshnessStatus"], "stale")
        self.assertEqual(detail["retrievalObservations"][0]["coverageStatus"], "unknown")

    def test_malformed_row_remains_a_distinct_occurrence_while_valid_rows_are_usable(self) -> None:
        payload = json.dumps(
            [
                {"filing_id": "house_20030001", "ticker": "ABC"},
                "source row could not be interpreted",
            ],
            separators=(",", ":"),
        ).encode()

        result = self._ingest_supporting(payload, retrieved_at_ms=1_800_000_000_000)
        rows = self.application.query_evidence(population="test")["artifacts"][0]["versions"][0][
            "rowOccurrences"
        ]

        self.assertEqual(result["parseStatus"], "partial")
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["parseStatus"], "parsed")
        self.assertEqual(rows[1]["parseStatus"], "malformed")
        self.assertEqual(rows[1]["rawFields"], "source row could not be interpreted")

    def test_house_index_discovers_filings_without_treating_index_records_as_transactions(self) -> None:
        content = self._house_index_zip(
            [
                {
                    "Prefix": "Hon.",
                    "Last": "Aderholt",
                    "First": "Robert",
                    "Suffix": "",
                    "FilingType": "P",
                    "StateDst": "AL04",
                    "Year": "2025",
                    "FilingDate": "9/10/2025",
                    "DocID": "20032062",
                },
                {
                    "Prefix": "",
                    "Last": "Example",
                    "First": "Alex",
                    "Suffix": "",
                    "FilingType": "A",
                    "StateDst": "CA01",
                    "Year": "2025",
                    "FilingDate": "",
                    "DocID": "20032063",
                },
            ]
        )

        result = self.application.ingest_house_index(
            RetrievedArtifact(
                population="test",
                source_name="house-clerk",
                source_url="https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025FD.ZIP",
                media_type="application/zip",
                content=content,
                retrieved_at_ms=1_800_000_000_000,
                purpose="daily_discovery",
                freshness_status="unknown",
                coverage_status="unknown",
            ),
            report_year=2025,
        )
        evidence = self.application.query_evidence(population="test")

        self.assertEqual(result["parseStatus"], "succeeded")
        self.assertEqual(result["sourceFilingsDiscovered"], 2)
        self.assertEqual(result["filingDocumentIds"], ["20032062"])
        self.assertEqual(len(evidence["sourceFilings"]), 2)
        self.assertEqual(evidence["sourceFilings"][1]["rawMetadata"]["FilingType"], "A")
        self.assertEqual(evidence["sourceFilings"][1]["rawMetadata"]["FilingDate"], "")
        version = evidence["artifacts"][0]["versions"][0]
        self.assertEqual(version["rowOccurrences"], [])
        self.assertEqual(version["extractions"][0]["representation"][1]["DocID"], "20032063")
        self.assertEqual(
            evidence["sourceFilings"][1]["evidence"][0]["artifactVersionId"],
            version["id"],
        )

    def test_official_and_supporting_representations_remain_separately_attributed(self) -> None:
        official = self.application.ingest_house_filing(
            RetrievedArtifact(
                population="test",
                source_name="house-clerk",
                source_url="https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20032062.pdf",
                media_type="application/pdf",
                content=b"%PDF official filing content naming ABC",
                retrieved_at_ms=1_800_000_000_000,
                purpose="daily_discovery",
                freshness_status="unknown",
                coverage_status="unknown",
            ),
            report_year=2025,
            document_id="20032062",
        )
        supporting = self._ingest_supporting(
            json.dumps(
                [{"filing_id": "house_20032062", "ticker": "XYZ"}],
                separators=(",", ":"),
            ).encode(),
            retrieved_at_ms=1_800_000_060_000,
        )
        evidence = self.application.query_evidence(population="test")

        self.assertNotEqual(official["artifactId"], supporting["artifactId"])
        self.assertEqual(
            {artifact["sourceAuthority"] for artifact in evidence["artifacts"]},
            {"official", "supporting"},
        )
        self.assertEqual(
            {(filing["sourceName"], filing["sourceFilingId"]) for filing in evidence["sourceFilings"]},
            {("house-clerk", "20032062"), ("kadoa", "house_20032062")},
        )
        self.assertEqual(official["parseStatus"], "failed")

    def test_original_values_coexist_with_versioned_extraction_and_normalization(self) -> None:
        result = self._ingest_supporting(
            json.dumps(
                [
                    {
                        "filing_id": "house_20030001",
                        "ticker": " abc ",
                        "amount": "  $1,001 - $15,000  ",
                        "transaction_date": "10/02/2025",
                        "disclosure_date": "10/01/2025",
                    }
                ],
                separators=(",", ":"),
            ).encode(),
            retrieved_at_ms=1_800_000_000_000,
        )
        before = self.application.query_evidence(population="test")
        occurrence_id = before["artifacts"][0]["versions"][0]["rowOccurrences"][0]["id"]

        recomputed = self.application.reprocess_artifact_version(
            result["artifactVersionId"],
            population="test",
            extracted_at_ms=1_800_000_120_000,
            extraction_method_version="2",
            normalization_method_version="2",
        )
        after = self.application.query_evidence(population="test")
        version = after["artifacts"][0]["versions"][0]
        row = version["rowOccurrences"][0]

        self.assertEqual(recomputed["rowOccurrencesCreated"], 0)
        self.assertEqual(row["id"], occurrence_id)
        self.assertEqual(row["rawFields"]["ticker"], " abc ")
        self.assertEqual(row["rawFields"]["amount"], "  $1,001 - $15,000  ")
        self.assertEqual(len(version["extractions"]), 2)
        self.assertIsInstance(version["extractions"][0]["representation"], list)
        self.assertEqual(version["extractions"][1]["representation"]["container"], "list")
        self.assertEqual(
            [normalization["methodVersion"] for normalization in row["normalizations"]],
            ["1", "2"],
        )
        self.assertEqual(row["normalizations"][0]["extractionId"], version["extractions"][0]["id"])
        self.assertEqual(row["normalizations"][1]["extractionId"], version["extractions"][1]["id"])
        self.assertEqual(row["normalizations"][0]["normalizedFields"]["ticker"], "ABC")
        self.assertEqual(row["normalizations"][0]["normalizedFields"]["disclosureLatencyDays"], -1)
        self.assertIn("negative_disclosure_latency", row["normalizations"][0]["issues"])

    def test_normalization_recomputation_uses_a_distinct_versioned_method(self) -> None:
        result = self._ingest_supporting(
            json.dumps(
                [
                    {
                        "transaction_date": " 10/02/2025 ",
                        "disclosure_date": "10/01/2025",
                    }
                ],
                separators=(",", ":"),
            ).encode(),
            retrieved_at_ms=1_800_000_000_000,
        )

        self.application.reprocess_artifact_version(
            result["artifactVersionId"],
            population="test",
            extracted_at_ms=1_800_000_120_000,
            extraction_method_version="2",
            normalization_method_version="2",
        )
        row = self.application.query_evidence(population="test")["artifacts"][0]["versions"][0][
            "rowOccurrences"
        ][0]

        first, second = row["normalizations"]
        self.assertIn("malformed_transaction_date", first["issues"])
        self.assertNotIn("transactionDate", first["normalizedFields"])
        self.assertEqual(second["normalizedFields"]["transactionDate"], "2025-10-02")
        self.assertEqual(second["normalizedFields"]["disclosureLatencyDays"], -1)

    def test_fixture_populations_cannot_enter_real_queries(self) -> None:
        for index, population in enumerate(("demo", "test", "evaluation")):
            self.application.ingest_supporting_retrieval(
                RetrievedArtifact(
                    population=population,
                    source_name="kadoa",
                    source_url=f"https://supporting.example/{population}.json",
                    media_type="application/json",
                    content=b"[]",
                    retrieved_at_ms=1_800_000_000_000 + index,
                    purpose="manual",
                    freshness_status="unknown",
                    coverage_status="unknown",
                )
            )

        self.assertEqual(self.application.query_evidence(population="real")["artifacts"], [])
        self.assertEqual(len(self.application.query_evidence(population="demo")["artifacts"]), 1)
        self.assertEqual(len(self.application.query_evidence(population="test")["artifacts"]), 1)
        self.assertEqual(len(self.application.query_evidence(population="evaluation")["artifacts"]), 1)

    def test_chamber_readiness_stays_unavailable_without_every_approved_gate(self) -> None:
        self._ingest_supporting(b"[]", retrieved_at_ms=1_800_000_000_000)

        readiness = self.application.query_chamber_readiness(population="test")

        self.assertEqual(readiness["house"]["availability"], "unavailable")
        self.assertEqual(readiness["senate"]["availability"], "unavailable")
        self.assertEqual(
            {gate["code"] for gate in readiness["house"]["unmetPrerequisites"]},
            {
                "minimum_history_and_gaps",
                "original_artifact_retrieval",
                "amendment_and_backfill_behavior",
                "retention_permission",
                "daily_discovery",
                "downtime_catch_up",
                "older_additions_and_changes_reconciliation",
            },
        )

    @staticmethod
    def _house_index_zip(records: list[dict[str, str]]) -> bytes:
        xml_records = "".join(
            "<Member>"
            + "".join(f"<{key}>{value}</{key}>" for key, value in record.items())
            + "</Member>"
            for record in records
        )
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("2025FD.xml", f"<FinancialDisclosure>{xml_records}</FinancialDisclosure>")
        return buffer.getvalue()

    def _ingest_supporting(
        self,
        content: bytes,
        *,
        retrieved_at_ms: int,
        freshness_status: str = "current",
        coverage_status: str = "partial",
    ) -> dict:
        return self.application.ingest_supporting_retrieval(
            RetrievedArtifact(
                population="test",
                source_name="kadoa",
                source_url="https://supporting.example/house.json",
                media_type="application/json",
                content=content,
                retrieved_at_ms=retrieved_at_ms,
                purpose="reconciliation",
                freshness_status=freshness_status,
                coverage_status=coverage_status,
            )
        )


if __name__ == "__main__":
    unittest.main()
