import sqlite3
import tempfile
import unittest
import zipfile
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from disclosure_sources import FetchedSourceArtifact, house_filing_url, house_index_url
from disclosures import DisclosureApplication
from jobs.disclosures import run_daily_disclosure_discovery, run_startup_disclosure_catch_up
from jobs import scheduler


SCHEMA_PATH = Path(__file__).parents[1] / "db" / "schema.sql"


class FakeHouseSource:
    def __init__(self) -> None:
        self.filing_fetches: list[tuple[int, str]] = []
        self.filing_content = b"%PDF retained official filing"

    def fetch_index(self, report_year: int) -> FetchedSourceArtifact:
        buffer = BytesIO()
        xml = (
            "<FinancialDisclosure><Member>"
            f"<Year>{report_year}</Year><FilingType>P</FilingType>"
            f"<DocID>{report_year}001</DocID>"
            "</Member></FinancialDisclosure>"
        )
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(f"{report_year}FD.xml", xml)
        return FetchedSourceArtifact(
            source_url=house_index_url(report_year),
            media_type="application/zip",
            content=buffer.getvalue(),
            retrieved_at_ms=1_800_000_000_000 + report_year,
            http_status=200,
            availability_status="available",
            source_metadata={},
        )

    def fetch_filing(self, report_year: int, document_id: str) -> FetchedSourceArtifact:
        self.filing_fetches.append((report_year, document_id))
        return FetchedSourceArtifact(
            source_url=house_filing_url(report_year, document_id),
            media_type="application/pdf",
            content=self.filing_content,
            retrieved_at_ms=1_800_000_100_000 + report_year,
            http_status=200,
            availability_status="available",
            source_metadata={},
        )


class DisclosureJobsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "signal-jobs-test.db"
        with self.connection() as conn:
            conn.executescript(SCHEMA_PATH.read_text())
        self.application = DisclosureApplication(self.connection)
        self.source = FakeHouseSource()

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

    def test_startup_and_daily_runs_record_catch_up_discovery_and_older_reconciliation(self) -> None:
        run_startup_disclosure_catch_up(
            application=self.application,
            source=self.source,
            report_years=[2025],
        )
        run_daily_disclosure_discovery(
            application=self.application,
            source=self.source,
            current_report_year=2026,
            reconciliation_years=[2025],
        )

        artifacts = self.application.query_evidence(population="real")["artifacts"]
        purposes_by_url = {
            artifact["sourceUrl"]: [
                observation["purpose"] for observation in artifact["retrievalObservations"]
            ]
            for artifact in artifacts
        }
        self.assertCountEqual(
            purposes_by_url[house_index_url(2025)],
            ["startup_catch_up", "reconciliation"],
        )
        self.assertEqual(purposes_by_url[house_index_url(2026)], ["daily_discovery"])
        self.assertCountEqual(
            purposes_by_url[house_filing_url(2025, "2025001")],
            ["startup_catch_up", "reconciliation"],
        )
        self.assertEqual(purposes_by_url[house_filing_url(2026, "2026001")], ["daily_discovery"])
        self.assertEqual(
            self.source.filing_fetches,
            [(2025, "2025001"), (2026, "2026001"), (2025, "2025001")],
        )
        index_artifact = next(
            artifact for artifact in artifacts if artifact["sourceUrl"] == house_index_url(2025)
        )
        filing_artifact = next(
            artifact
            for artifact in artifacts
            if artifact["sourceUrl"] == house_filing_url(2025, "2025001")
        )
        self.assertEqual(len(index_artifact["versions"]), 1)
        self.assertEqual(len(filing_artifact["versions"]), 1)

    def test_reconciliation_detects_changed_original_filing_bytes(self) -> None:
        run_startup_disclosure_catch_up(
            application=self.application,
            source=self.source,
            report_years=[2025],
        )
        self.source.filing_content = b"%PDF changed official filing"

        run_daily_disclosure_discovery(
            application=self.application,
            source=self.source,
            current_report_year=2026,
            reconciliation_years=[2025],
        )

        artifacts = self.application.query_evidence(population="real")["artifacts"]
        filing_artifact = next(
            artifact
            for artifact in artifacts
            if artifact["sourceUrl"] == house_filing_url(2025, "2025001")
        )
        self.assertEqual(len(filing_artifact["versions"]), 2)
        self.assertCountEqual(
            [item["purpose"] for item in filing_artifact["retrievalObservations"]],
            ["startup_catch_up", "reconciliation"],
        )

    def test_scheduler_registers_startup_and_source_local_daily_discovery(self) -> None:
        class RecordingScheduler:
            def __init__(self):
                self.jobs = []
                self.started = False

            def add_job(self, func, trigger, **kwargs):
                self.jobs.append((func, trigger, kwargs))

            def start(self):
                self.started = True

        recording = RecordingScheduler()
        with patch.object(scheduler, "_scheduler", recording):
            scheduler.start_scheduler()

        jobs = {kwargs.get("id"): (func, trigger, kwargs) for func, trigger, kwargs in recording.jobs}
        self.assertIn("disclosure-startup-catch-up", jobs)
        self.assertIn("disclosure-daily-discovery", jobs)
        _, trigger, daily = jobs["disclosure-daily-discovery"]
        self.assertEqual(trigger, "cron")
        self.assertEqual(daily["timezone"], "America/New_York")


if __name__ == "__main__":
    unittest.main()
