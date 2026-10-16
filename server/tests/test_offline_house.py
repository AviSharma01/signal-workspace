"""API acceptance for the fixed corpus; every write uses a temporary database."""
import hashlib
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from unittest.mock import patch

from fastapi.testclient import TestClient

from db import database
from main import app
from offline_house import CORPUS, CorpusEntry
from house_ptr import extract_ptr


BASE = "/api/disclosures/offline-corpus"
SIMPLE = "2021-20018021"

# A separate OS process dies at the SQLite commit seam. This exercises actual
# persisted records/journal rollback rather than manufacturing recovery states.
CRASH_PROCESS = r'''
import os, sqlite3, sys
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from db import database
database.DB_PATH = Path(sys.argv[1])
from main import app
original_connect = sqlite3.connect
class InterruptedConnection(sqlite3.Connection):
    touched = False
    def execute(self, sql, *args, **kwargs):
        result = super().execute(sql, *args, **kwargs)
        if sql.lstrip().startswith('INSERT INTO ' + sys.argv[2]):
            self.touched = True
        return result
    def commit(self):
        if self.touched and sys.argv[3] == 'before':
            os._exit(73)
        super().commit()
        if self.touched:
            os._exit(73)
def connect(*args, **kwargs):
    return original_connect(*args, **kwargs, factory=InterruptedConnection)
with patch('db.database.sqlite3.connect', side_effect=connect), \
     patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden')):
    client = TestClient(app, base_url='http://localhost:8000', client=('127.0.0.1', 50000))
    key = sys.argv[4] if len(sys.argv) > 4 else '2021-20018021'
    client.post('/api/disclosures/offline-corpus/'+key+'/observations', json={})
raise AssertionError('Crash seam was not reached')
'''

RESTART_PROCESS = r'''
import json, sys
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from db import database
database.DB_PATH = Path(sys.argv[1])
from main import app
with patch('urllib.request.urlopen', side_effect=AssertionError('Network forbidden')), \
     patch('socket.socket.connect', side_effect=AssertionError('Network forbidden')):
    with TestClient(app, base_url='http://localhost:8000', client=('127.0.0.1', 50000)) as client:
        path = '/api/disclosures/offline-corpus'
        key = sys.argv[2] if len(sys.argv) > 2 else '2021-20018021'
        before = next(e for e in client.get(path).json()['entries'] if e['key'] == key)
        action = 'resume' if before['imported'] else 'observations'
        result = client.post(path+'/'+key+'/'+action, json={})
        assert result.status_code in (200, 201), result.text
        after = next(e for e in client.get(path).json()['entries'] if e['key'] == key)
        print(json.dumps({'before':before['processingStatus'], 'after':after}))
'''


class OfflineHouseTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "offline.db"
        self.selection = patch.object(database, "DB_PATH", self.path)
        self.selection.start()
        self.addCleanup(self.selection.stop)
        self.addCleanup(self.directory.cleanup)
        database.init_db()
        self.network = patch("urllib.request.urlopen", side_effect=AssertionError("Network forbidden"))
        self.network.start()
        self.addCleanup(self.network.stop)
        self.client = TestClient(app, base_url="http://localhost:8000", client=("127.0.0.1", 50000))
        self.addCleanup(self.client.close)

    def corpus(self):
        response = self.client.get(BASE)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def command(self, key=SIMPLE, action="observations"):
        return self.client.post(f"{BASE}/{key}/{action}", json={})

    def test_fresh_declarations_are_not_imports_or_observations(self):
        corpus = self.corpus()
        self.assertEqual(corpus["importedCount"], 0)
        self.assertEqual(len(corpus["entries"]), 6)
        for entry in corpus["entries"]:
            self.assertFalse(entry["imported"])
            self.assertIsNone(entry["artifact"])
            self.assertIsNone(entry["sourceFiling"])
            self.assertEqual(entry["processingStatus"], "not_imported")
            self.assertEqual(entry["extractionStatus"], "not_attempted")
            self.assertIsNone(entry["receipt"]["extractedRowStarts"])
            self.assertEqual(entry["receipt"]["completeness"], "unknown")
        self.assertEqual(self.command(action="resume").status_code, 409)
        with database.get_connection() as conn:
            self.assertEqual(conn.execute("SELECT count(*) FROM disclosure_retrieval_observations").fetchone()[0], 0)

    def test_six_files_reconcile_repeated_reads_and_no_observation_resumes(self):
        expected = [(1, "succeeded"), (5, "succeeded"), (33, "succeeded"),
                    (0, "unsupported"), (5, "succeeded"), (296, "partial")]
        for entry in CORPUS:
            response = self.command(entry.key)
            self.assertEqual(response.status_code, 201, response.text)
        before = self.corpus()
        self.assertEqual(before["importedCount"], 6)
        for entry, (count, outcome), declared in zip(before["entries"], expected, CORPUS):
            self.assertEqual(entry["processingStatus"], "finished")
            self.assertEqual(entry["extractionStatus"], outcome)
            self.assertEqual(entry["receipt"]["storedRows"], count)
            self.assertEqual(entry["receipt"]["normalizedRows"], count)
            self.assertEqual(entry["sourceFiling"]["sourceFilingId"], declared.document_id)
            artifact = entry["artifact"]
            version = artifact["versions"][0]
            content = self.client.get(f'{BASE}/artifacts/{artifact["id"]}/versions/{version["id"]}/content')
            self.assertEqual(content.status_code, 200)
            self.assertEqual(hashlib.sha256(content.content).hexdigest(), declared.sha256)
            observation = artifact["retrievalObservations"][0]
            self.assertIsNone(observation["httpStatus"])
            self.assertIsNone(observation["sourceMetadata"]["originalRetrievedAt"])
            self.assertEqual(observation["freshnessStatus"], "unknown")
            self.assertEqual(self.command(declared.key, "resume").status_code, 200)
        self.assertEqual(self.corpus(), before)
        for declared in CORPUS:
            self.assertEqual(self.command(declared.key).status_code, 201)
        after = self.corpus()
        for first, second in zip(before["entries"], after["entries"]):
            self.assertEqual(first["receipt"], second["receipt"])
            self.assertEqual(first["artifact"]["versions"], second["artifact"]["versions"])
            self.assertEqual(len(second["artifact"]["retrievalObservations"]), 2)
        self.assertEqual(after["entries"][-1]["receipt"]["unresolvedFragmentCount"], 2)
        self.assertEqual(after["entries"][-1]["receipt"]["partialRows"], 2)
        self.assertEqual(after["entries"][3]["receipt"]["completeness"], "unknown")
        self.assertEqual(after["entries"][-1]["receipt"]["completeness"], "partial")
        old_rows = after["entries"][4]["artifact"]["versions"][0]["rowOccurrences"]
        self.assertEqual(len({r["id"] for r in old_rows[2:]}), 3)

    def test_population_route_and_mutation_isolation(self):
        self.assertEqual(self.command().status_code, 201)
        entry = self.corpus()["entries"][0]
        artifact = entry["artifact"]
        version = artifact["versions"][0]
        self.assertEqual(self.client.get("/api/disclosures/evidence").json()["artifacts"], [])
        self.assertEqual(self.client.get("/api/watch-events").json()["watchEvents"], [])
        self.assertEqual(self.client.get("/api/findings").json()["findings"], [])
        self.assertEqual(self.client.get(f'/api/disclosures/artifacts/{artifact["id"]}/versions/{version["id"]}').status_code, 404)
        for body in [{"population":"real"}, {"path":"/etc/passwd"}, {"sourceUrl":"https://example.org"}, {"payloadBase64":"AA=="}]:
            self.assertEqual(self.client.post(f"{BASE}/{SIMPLE}/observations", json=body).status_code, 422)
        self.assertEqual(self.command("undeclared").status_code, 404)
        self.assertEqual(self.client.post(f"{BASE}/{SIMPLE}/resume", json={}, headers={"Origin":"https://example.org"}).status_code, 403)
        self.assertEqual(self.client.post("/api/disclosures/house/filings/2021/20018021/retrievals", json={"purpose":"manual"}).status_code, 409)
        capabilities = {c["id"]: c for c in self.client.get("/api/capabilities").json()["capabilities"]}
        self.assertEqual(capabilities["market.outcomes"]["availability"], "unavailable")

    def test_missing_tampered_and_aliased_fixtures_do_not_create_evidence(self):
        with tempfile.TemporaryDirectory() as temporary, patch("offline_house.FIXTURE_ROOT", Path(temporary).resolve()):
            path = Path(temporary) / f"{SIMPLE}.pdf"
            self.assertEqual(self.command().status_code, 503)
            path.write_bytes(b"synthetic tampered bytes")
            self.assertEqual(self.command().status_code, 409)
            path.unlink()
            path.symlink_to(Path(__file__).parent / "fixtures/house_ptr" / f"{SIMPLE}.pdf")
            self.assertEqual(self.command().status_code, 409)
        self.assertEqual(self.corpus()["importedCount"], 0)

    def test_resume_survives_missing_fixture_but_blocks_corrupt_database_bytes(self):
        self.assertEqual(self.command().status_code, 201)
        before = self.corpus()["entries"][0]
        with tempfile.TemporaryDirectory() as temporary, patch("offline_house.FIXTURE_ROOT", Path(temporary).resolve()):
            self.assertEqual(self.command(action="resume").status_code, 200)
            self.assertEqual(self.corpus()["entries"][0]["localCopyStatus"], "missing")
        self.assertEqual(self.corpus()["entries"][0], before)
        with database.get_connection() as conn:
            conn.execute("UPDATE disclosure_artifact_versions SET raw_content = ?", (b"synthetic corruption",))
        corrupt = self.corpus()["entries"][0]
        self.assertEqual(corrupt["processingStatus"], "integrity_error")
        self.assertEqual(self.command(action="resume").status_code, 409)
        self.assertEqual(self.command().status_code, 409)
        artifact = corrupt["artifact"]
        self.assertEqual(self.client.get(f'{BASE}/artifacts/{artifact["id"]}/versions/{artifact["versions"][0]["id"]}/content').status_code, 409)
        self.assertEqual(len(self.corpus()["entries"][0]["artifact"]["retrievalObservations"]), 1)

    def test_retryable_database_failure_is_visible_and_resume_adds_no_read(self):
        with patch("disclosures.DisclosureApplication._process_house_ptr", side_effect=sqlite3.OperationalError("database is locked")):
            response = self.command()
        self.assertEqual(response.status_code, 503)
        self.assertTrue(response.json()["detail"]["retryable"])
        self.assertEqual(self.corpus()["entries"][0]["processingStatus"], "extraction_pending")
        self.assertEqual(self.command(action="resume").status_code, 200)
        self.assertEqual(len(self.corpus()["entries"][0]["artifact"]["retrievalObservations"]), 1)

    def test_concurrent_imports_and_resumes_converge(self):
        for actions in [("observations", "observations"), ("resume", "resume"), ("observations", "resume")]:
            with self.subTest(actions=actions):
                # Leave a real committed raw/link stage for the resume scenarios.
                if "resume" in actions:
                    with database.get_connection() as conn:
                        conn.execute("DELETE FROM disclosure_normalizations")
                        conn.execute("DELETE FROM disclosure_source_filing_evidence")
                        conn.execute("DELETE FROM disclosure_row_occurrences")
                        conn.execute("DELETE FROM disclosure_extractions")
                barrier = Barrier(2)
                def extract_together(content):
                    barrier.wait(timeout=10)
                    return extract_ptr(content)
                with patch("disclosures.extract_ptr", side_effect=extract_together), ThreadPoolExecutor(max_workers=2) as pool:
                    responses = list(pool.map(lambda action: self.command(action=action), actions))
                self.assertEqual([r.status_code for r in responses], [201 if a == "observations" else 200 for a in actions])
                entry = self.corpus()["entries"][0]
                self.assertEqual(entry["processingStatus"], "finished")
                self.assertEqual(len(entry["artifact"]["versions"]), 1)
                self.assertEqual(entry["receipt"]["storedRows"], 1)
                self.assertEqual(entry["receipt"]["normalizedRows"], 1)
        self.assertEqual(len(entry["artifact"]["retrievalObservations"]), 3)

    def test_synthetic_parse_failure_is_preserved_as_finished_with_unknown_completeness(self):
        content = b"Not a PDF: synthetic negative fixture"
        synthetic = CorpusEntry(SIMPLE, hashlib.sha256(content).hexdigest(), len(content), 0, None, "Synthetic failure fixture")
        with tempfile.TemporaryDirectory() as temporary, patch("offline_house.FIXTURE_ROOT", Path(temporary).resolve()), patch("offline_house.CORPUS", (synthetic,)):
            (Path(temporary) / f"{SIMPLE}.pdf").write_bytes(content)
            with patch("disclosures.DisclosureApplication._link_source_filing_evidence", side_effect=sqlite3.OperationalError("database is locked")):
                self.assertEqual(self.command().status_code, 503)
            entry = self.corpus()["entries"][0]
            self.assertEqual(entry["extractionStatus"], "failed")
            self.assertEqual(entry["processingStatus"], "filing_evidence_pending")
            self.assertEqual(entry["receipt"]["completeness"], "unknown")
            self.assertEqual(self.command(action="resume").status_code, 200)
            self.assertEqual(self.corpus()["entries"][0]["processingStatus"], "finished")

    def test_scan_crash_after_extraction_is_pending_until_filing_evidence_is_linked(self):
        key = "2018-9113416"
        cwd = Path(__file__).parents[1]
        crashed = subprocess.run([sys.executable, "-B", "-c", CRASH_PROCESS, str(self.path), "disclosure_extractions", "after", key], cwd=cwd, capture_output=True, text=True, timeout=25)
        self.assertEqual(crashed.returncode, 73, crashed.stderr)
        scan = next(e for e in self.corpus()["entries"] if e["key"] == key)
        self.assertEqual(scan["processingStatus"], "filing_evidence_pending")
        self.assertEqual(scan["extractionStatus"], "unsupported")
        restarted = subprocess.run([sys.executable, "-B", "-c", RESTART_PROCESS, str(self.path), key], cwd=cwd, capture_output=True, text=True, timeout=25)
        self.assertEqual(restarted.returncode, 0, restarted.stderr)
        after = json.loads(restarted.stdout)["after"]
        self.assertEqual(after["processingStatus"], "finished")
        self.assertEqual(after["extractionStatus"], "unsupported")
        self.assertEqual(after["receipt"]["completeness"], "unknown")
        self.assertEqual(len(after["sourceFiling"]["evidence"]), 1)
        self.assertEqual(len(after["artifact"]["retrievalObservations"]), 1)

    def test_cold_restart_recovers_each_commit_boundary(self):
        stages = ["disclosure_retrieval_observations", "disclosure_extractions", "disclosure_row_occurrences", "disclosure_normalizations"]
        for stage in stages:
            for side in ("before", "after"):
                with self.subTest(stage=stage, side=side), tempfile.TemporaryDirectory() as directory:
                    selected = Path(directory) / "crash.db"
                    with patch.object(database, "DB_PATH", selected):
                        database.init_db()
                    cwd = Path(__file__).parents[1]
                    crashed = subprocess.run([sys.executable, "-B", "-c", CRASH_PROCESS, str(selected), stage, side], cwd=cwd, capture_output=True, text=True, timeout=25)
                    self.assertEqual(crashed.returncode, 73, crashed.stderr)
                    restarted = subprocess.run([sys.executable, "-B", "-c", RESTART_PROCESS, str(selected)], cwd=cwd, capture_output=True, text=True, timeout=25)
                    self.assertEqual(restarted.returncode, 0, restarted.stderr)
                    result = json.loads(restarted.stdout)
                    after = result["after"]
                    self.assertEqual(after["processingStatus"], "finished")
                    self.assertEqual(after["receipt"]["storedRows"], 1)
                    self.assertEqual(after["receipt"]["normalizedRows"], 1)
                    self.assertEqual(len(after["artifact"]["retrievalObservations"]), 1)
                    if stage == stages[0] and side == "before":
                        self.assertEqual(result["before"], "not_imported")
                    with patch.object(database, "DB_PATH", selected), database.get_connection() as conn:
                        self.assertEqual(conn.execute("PRAGMA quick_check").fetchone()[0], "ok")
                        self.assertEqual(conn.execute("PRAGMA foreign_key_check").fetchall(), [])
