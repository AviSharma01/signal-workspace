import hashlib
import sqlite3
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pdfplumber

from disclosures import DisclosureApplication, RetrievedArtifact
from tests.ptr_pdf_fixture import ptr_pdf


FIXTURES = Path(__file__).parent / "fixtures" / "house_ptr"


class HousePtrTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "ptr-test.db"
        with self.connection() as conn:
            conn.executescript((Path(__file__).parents[1] / "db/schema.sql").read_text())
        self.application = DisclosureApplication(self.connection)

    def tearDown(self):
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

    def ingest(self, name, *, content=None, observed_at=1_800_000_000_000):
        year, document_id = name.removesuffix(".pdf").split("-")
        return self.application.ingest_house_filing(
            RetrievedArtifact(
                population="test", source_name="house-clerk",
                source_url=f"https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/{year}/{document_id}.pdf",
                media_type="application/pdf",
                content=content if content is not None else (FIXTURES / name).read_bytes(),
                retrieved_at_ms=observed_at, purpose="manual",
                freshness_status="unknown", coverage_status="unknown",
            ), report_year=int(year), document_id=document_id,
        )

    def test_official_pdf_yields_transaction_occurrence_with_exact_artifact_provenance(self):
        result = self.ingest("2021-20018021.pdf")
        evidence = self.application.query_evidence(population="test")
        artifact = evidence["artifacts"][0]
        version = artifact["versions"][0]
        self.assertEqual(result["rowOccurrencesCreated"], 1)
        self.assertEqual(artifact["sourceAuthority"], "official")
        self.assertEqual(version["contentSha256"], hashlib.sha256(
            (FIXTURES / "2021-20018021.pdf").read_bytes()).hexdigest())
        extraction = version["extractions"][0]
        self.assertEqual(extraction["method"], "house-ptr-native-table")
        self.assertEqual(extraction["methodVersion"], "1")
        self.assertEqual(extraction["status"], "succeeded")
        row = version["rowOccurrences"][0]
        self.assertEqual(row["rawFields"]["asset"], "Dominion Energy, Inc. (D) [ST]")
        self.assertEqual(row["rawFields"]["owner"], "SP")
        self.assertEqual(row["rawFields"]["transaction_date"], "12/15/2020")
        self.assertEqual(row["rawFields"]["sourcePosition"]["page"], 1)
        self.assertEqual(row["sourceFiling"]["sourceFilingId"], "20018021")
        self.assertEqual(row["normalizations"][0]["extractionId"], extraction["id"])
        self.assertEqual(row["normalizations"][0]["normalizedFields"]["transactionDate"], "2020-12-15")
        self.assertNotIn("disclosureDate", row["normalizations"][0]["normalizedFields"])
        self.assertIn("Dominion Energy", extraction["representation"]["pages"][0]["text"])

    def test_old_and_new_layouts_preserve_literal_ids_and_identical_occurrences(self):
        self.ingest("2018-20010021.pdf")
        self.ingest("2026-20034556.pdf", observed_at=1_800_000_001_000)
        artifacts = self.application.query_evidence(population="test")["artifacts"]
        old = artifacts[0]["versions"][0]["rowOccurrences"]
        newer = artifacts[1]["versions"][0]["rowOccurrences"]
        self.assertEqual(len(old), 5)
        self.assertEqual(len(newer), 5)
        self.assertEqual([r["rawFields"]["asset"] for r in old[2:]], ["Walt Disney Company (DIS) [ST]"] * 3)
        self.assertEqual(len({r["id"] for r in old[2:]}), 3)
        self.assertEqual(len({str(r["rawFields"]["sourcePosition"]) for r in old[2:]}), 3)
        self.assertEqual(newer[1]["rawFields"]["reported_id"], "2000152177")
        self.assertEqual(newer[1]["rawFields"]["transaction_type"], "S (partial)")
        self.assertNotIn("amendment", newer[1])

    def test_multiple_pages_retain_all_rows_and_do_not_count_continuation_fragments_twice(self):
        self.ingest("2025-20030699.pdf")
        self.ingest("2025-20030387.pdf", observed_at=1_800_000_001_000)
        artifacts = self.application.query_evidence(population="test")["artifacts"]
        short, long = [a["versions"][0] for a in artifacts]
        # Counts independently checked against the PDFs' paired-date transaction lines.
        self.assertEqual(len(short["rowOccurrences"]), 33)
        self.assertEqual(len(long["rowOccurrences"]), 296)
        self.assertEqual(len(short["extractions"][0]["representation"]["pages"]), 5)
        self.assertEqual(len(long["extractions"][0]["representation"]["pages"]), 41)
        self.assertEqual(long["extractions"][0]["status"], "partial")
        self.assertEqual(len(long["extractions"][0]["representation"]["unresolvedFragments"]), 2)
        self.assertEqual(sum(r["parseStatus"] == "partial" for r in long["rowOccurrences"]), 2)

    def test_scanned_and_invalid_pdfs_retain_evidence_without_inventing_rows(self):
        for name, content, expected in (
            ("2018-9113416.pdf", None, "unsupported"),
            ("2021-20018021.pdf", b"broken PDF", "failed"),
        ):
            result = self.ingest(name, content=content)
            self.assertEqual(result["parseStatus"], expected)
            self.assertEqual(result["rowOccurrencesCreated"], 0)
            detail = self.application.get_artifact_version(result["artifactId"], result["artifactVersionId"], population="test")
            self.assertEqual(detail["rawContent"], content if content is not None else (FIXTURES / name).read_bytes())
            self.assertEqual(len(detail["retrievalObservations"]), 1)

    def test_retrieval_replay_recomputation_and_changed_versions_preserve_occurrences(self):
        name = "2021-20018021.pdf"
        first = self.ingest(name)
        second = self.ingest(name, observed_at=1_800_000_001_000)
        before = self.application.query_evidence(population="test")
        rerun = self.application.reprocess_artifact_version(
            first["artifactVersionId"], population="test", extracted_at_ms=1_800_000_002_000,
            extraction_method_version="1", normalization_method_version="1",
        )
        self.assertEqual(first["artifactVersionId"], second["artifactVersionId"])
        self.assertEqual(second["rowOccurrencesCreated"], 0)
        self.assertEqual(rerun["rowOccurrencesCreated"], 0)
        self.assertEqual(self.application.query_evidence(population="test"), before)
        with self.assertRaises(ValueError):
            self.application.reprocess_artifact_version(
                first["artifactVersionId"], population="test", extracted_at_ms=1_800_000_002_000,
                extraction_method_version="2", normalization_method_version="2",
            )
        changed = self.ingest(name, content=(FIXTURES / name).read_bytes() + b"\n% changed retained bytes\n", observed_at=1_800_000_003_000)
        self.assertNotEqual(first["artifactVersionId"], changed["artifactVersionId"])
        versions = self.application.query_evidence(population="test")["artifacts"][0]["versions"]
        self.assertNotEqual(versions[0]["rowOccurrences"][0]["id"], versions[1]["rowOccurrences"][0]["id"])
        self.assertNotEqual(versions[0]["extractions"][0]["id"], versions[1]["extractions"][0]["id"])

    def test_missing_and_malformed_cells_are_retained_without_fabricating_fields(self):
        pdf = ptr_pdf([
            ["", "SP", "Synthetic Corp", "P", "nonsense", "", "unknown", ""],
            ["", "SP", "Synthetic Corp", "P", "nonsense", "", "unknown", ""],
        ])
        self.ingest("2021-20018021.pdf", content=pdf)
        version = self.application.query_evidence(population="test")["artifacts"][0]["versions"][0]
        self.assertEqual(version["extractions"][0]["status"], "partial")
        rows = version["rowOccurrences"]
        self.assertEqual(len(rows), 2)
        self.assertNotEqual(rows[0]["id"], rows[1]["id"])
        for row in rows:
            self.assertEqual(row["parseStatus"], "partial")
            self.assertEqual(row["rawFields"]["transaction_date"], "nonsense")
            self.assertEqual(row["rawFields"]["notification_date"], "")
            normalized = row["normalizations"][0]
            self.assertEqual(normalized["status"], "partial")
            self.assertIn("malformed_transaction_date", normalized["issues"])
            self.assertNotIn("transactionDate", normalized["normalizedFields"])
            self.assertNotIn("amountLower", normalized["normalizedFields"])

    def test_official_and_supporting_matching_values_cannot_overwrite_each_other(self):
        self.ingest("2021-20018021.pdf")
        self.application.ingest_supporting_retrieval(RetrievedArtifact(
            population="test", source_name="kadoa", source_url="https://supporting.example/rows",
            media_type="application/json", content=b'[{"filing_id":"20018021","asset":"Dominion Energy, Inc. (D) [ST]"}]',
            retrieved_at_ms=1_800_000_000_000, purpose="manual", freshness_status="unknown", coverage_status="unknown",
        ))
        artifacts = self.application.query_evidence(population="test")["artifacts"]
        self.assertEqual({a["sourceAuthority"] for a in artifacts}, {"official", "supporting"})
        self.assertEqual(sum(len(a["versions"][0]["rowOccurrences"]) for a in artifacts), 2)

    def test_later_pdf_page_failure_retains_earlier_rows_with_partial_extraction_status(self):
        read_words = pdfplumber.page.Page.extract_words

        def unavailable_page(page, **kwargs):
            if page.page_number == 2:
                raise OSError("injected PDF engine page-read failure")
            return read_words(page, **kwargs)

        # Fault injection at the external PDF engine boundary after a real page
        # is parsed, while the application/extraction/persistence remain real.
        with patch.object(pdfplumber.page.Page, "extract_words", new=unavailable_page):
            result = self.ingest("2025-20030699.pdf")
        version = self.application.query_evidence(population="test")["artifacts"][0]["versions"][0]
        self.assertEqual(result["parseStatus"], "partial")
        self.assertEqual(len(version["rowOccurrences"]), 6)
        extraction = version["extractions"][0]
        self.assertEqual(extraction["status"], "partial")
        self.assertTrue(any(issue.startswith("pdf_read_error:") for issue in extraction["representation"]["issues"]))

    def test_existing_unsupported_extraction_is_preserved_when_native_method_is_applied(self):
        # Retained pre-extractor state, not a private-helper mock. This is the
        # exact persisted contract that existed before the handoff repair.
        content = (FIXTURES / "2021-20018021.pdf").read_bytes()
        with self.connection() as conn:
            conn.execute("INSERT INTO disclosure_source_filings VALUES ('filing','test','house-clerk','20018021','house',NULL,1,'{}')")
            conn.execute("INSERT INTO disclosure_artifacts VALUES ('artifact','test','house-clerk','official','original_filing','filing','official-url','application/pdf',1)")
            conn.execute("INSERT INTO disclosure_artifact_versions VALUES ('version','artifact',?,?,?,'application/pdf',1)", (hashlib.sha256(content).hexdigest(), content, len(content)))
            conn.execute("INSERT INTO disclosure_retrieval_observations VALUES ('observation','artifact','version',1,'manual','available','unknown','unknown',200,'{}')")
            conn.execute("INSERT INTO disclosure_extractions VALUES ('legacy','version','none','1',1,'unsupported',NULL,'No approved original-filing extractor is configured')")
        result = self.application.reprocess_artifact_version(
            "version", population="test", extracted_at_ms=1_800_000_000_000,
            extraction_method_version="1", normalization_method_version="1",
        )
        version = self.application.query_evidence(population="test")["artifacts"][0]["versions"][0]
        self.assertEqual(result["rowOccurrencesCreated"], 1)
        self.assertEqual([(x["method"], x["status"]) for x in version["extractions"]],
                         [("none", "unsupported"), ("house-ptr-native-table", "succeeded")])
        self.assertNotEqual(version["rowOccurrences"][0]["normalizations"][0]["extractionId"], "legacy")
