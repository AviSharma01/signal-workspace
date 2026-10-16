import hashlib
import os
import sqlite3
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from db import database
from main import app


class F2DatabaseTest(unittest.TestCase):
    def test_fresh_runtime_database_is_empty_owned_and_can_reopen_without_losing_data(self):
        with tempfile.TemporaryDirectory() as directory:
            local = Path(directory).resolve() / '.local'
            local.mkdir()
            selected = local / 'f2.db'
            with patch.object(database, 'DB_PATH', None), patch.object(database, 'LOCAL_DB_DIR', local), patch.dict(os.environ, {'SIGNAL_F2_DB': str(selected)}):
                database.init_db()
                with database.get_connection() as conn:
                    self.assertEqual(conn.execute('SELECT count(*) FROM companies').fetchone()[0], 0)
                    self.assertEqual(conn.execute('PRAGMA application_id').fetchone()[0], 0x53494732)
                    # Existing operator data must survive all later initialization.
                    conn.execute("INSERT INTO companies (id, name, population) VALUES ('EXISTING', 'Existing user record', 'real')")
                database.init_db()
                with database.get_connection() as conn:
                    self.assertEqual([tuple(row) for row in conn.execute('SELECT id, name, population FROM companies')],
                                     [('EXISTING', 'Existing user record', 'real')])

    def test_runtime_rejects_unrelated_databases_inside_and_outside_the_local_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            local = root / '.local'
            local.mkdir()
            for path in [root / 'unrelated.db', local / 'unrelated.db']:
                with sqlite3.connect(path) as conn:
                    conn.execute('CREATE TABLE user_documents (body TEXT)')
                    conn.execute("INSERT INTO user_documents VALUES ('preserve me')")
                before = hashlib.sha256(path.read_bytes()).hexdigest()
                with patch.object(database, 'DB_PATH', None), patch.dict(os.environ, {'SIGNAL_F2_DB': str(path)}):
                    # Model the approved local directory without touching the real one.
                    with patch.object(database, 'LOCAL_DB_DIR', local, create=True):
                        with self.assertRaises(ValueError):
                            database.init_db()
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), before)
                with sqlite3.connect(path) as conn:
                    self.assertEqual(conn.execute('SELECT body FROM user_documents').fetchone()[0], 'preserve me')

    def test_runtime_rejects_path_and_file_aliases_without_changing_their_targets(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            local = root / '.local'
            local.mkdir()
            external = root / 'protected.db'
            with sqlite3.connect(external) as conn:
                conn.execute('CREATE TABLE private_records (value TEXT)')
            before = hashlib.sha256(external.read_bytes()).hexdigest()
            (local / 'file-link.db').symlink_to(external)
            (local / 'directory-link').symlink_to(root, target_is_directory=True)
            os.link(external, local / 'hard-link.db')
            selections = [local / 'file-link.db', local / 'directory-link' / 'protected.db',
                          local / 'hard-link.db', local / '..' / 'protected.db']
            with patch.object(database, 'DB_PATH', None), patch.object(database, 'LOCAL_DB_DIR', local):
                for selected in selections:
                    with self.subTest(path=selected.name), patch.dict(os.environ, {'SIGNAL_F2_DB': str(selected)}):
                        with self.assertRaises(ValueError):
                            database.init_db()
                # The approved root itself must not be redirected elsewhere.
                redirected = root / 'redirected-local'
                redirected.symlink_to(local, target_is_directory=True)
                with patch.object(database, 'LOCAL_DB_DIR', redirected), patch.dict(os.environ, {'SIGNAL_F2_DB': str(redirected / 'new.db')}):
                    with self.assertRaises(ValueError):
                        database.init_db()
            self.assertFalse((local / 'new.db').exists())
            self.assertEqual(hashlib.sha256(external.read_bytes()).hexdigest(), before)

    def test_pre_marker_f2_schema_is_recognized_but_spoofed_or_empty_databases_are_not(self):
        with tempfile.TemporaryDirectory() as directory:
            local = Path(directory).resolve() / '.local'
            local.mkdir()
            selected = local / 'existing-f2.db'
            with sqlite3.connect(selected) as conn:
                conn.executescript(database.SCHEMA_PATH.read_text())
                conn.execute("INSERT INTO companies (id, name) VALUES ('KEPT', 'Existing user data')")
                self.assertEqual(conn.execute('PRAGMA application_id').fetchone()[0], 0)
            with patch.object(database, 'DB_PATH', None), patch.object(database, 'LOCAL_DB_DIR', local):
                with patch.dict(os.environ, {'SIGNAL_F2_DB': str(selected)}):
                    database.init_db()
                    database.init_db()
                    with database.get_connection() as conn:
                        self.assertEqual(conn.execute('PRAGMA application_id').fetchone()[0], 0x53494732)
                        self.assertEqual(conn.execute('SELECT name FROM companies').fetchone()[0], 'Existing user data')
                        self.assertEqual(conn.execute('PRAGMA quick_check').fetchone()[0], 'ok')
                        self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
                for name in ['empty.db', 'spoofed.db', 'wrong-owner.db']:
                    rejected = local / name
                    with sqlite3.connect(rejected) as conn:
                        if name == 'spoofed.db':
                            conn.execute('CREATE TABLE private_records (value TEXT)')
                            conn.execute('PRAGMA application_id = 1397311282')
                        elif name == 'wrong-owner.db':
                            conn.executescript(database.SCHEMA_PATH.read_text())
                            conn.execute('PRAGMA application_id = 123')
                    before = hashlib.sha256(rejected.read_bytes()).hexdigest()
                    with patch.dict(os.environ, {'SIGNAL_F2_DB': str(rejected)}):
                        with self.assertRaises(ValueError):
                            database.init_db()
                    self.assertEqual(hashlib.sha256(rejected.read_bytes()).hexdigest(), before)

    def test_even_recognized_f2_files_and_sidecars_cannot_be_hard_link_aliases(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            local = root / '.local'
            local.mkdir()
            selected = local / 'recognized.db'
            with patch.object(database, 'DB_PATH', None), patch.object(database, 'LOCAL_DB_DIR', local), patch.dict(os.environ, {'SIGNAL_F2_DB': str(selected)}):
                database.init_db()
                before = hashlib.sha256(selected.read_bytes()).hexdigest()
                os.link(selected, root / 'external-alias.db')
                with self.assertRaises(ValueError):
                    database.init_db()
                self.assertEqual(hashlib.sha256(selected.read_bytes()).hexdigest(), before)
                # A linked sidecar is also unsafe even when the DB is recognized.
                other = local / 'other.db'
                with patch.dict(os.environ, {'SIGNAL_F2_DB': str(other)}):
                    database.init_db()
                    other_before = hashlib.sha256(other.read_bytes()).hexdigest()
                    Path(str(other) + '-wal').symlink_to(selected)
                    with self.assertRaises(ValueError):
                        database.init_db()
                    self.assertEqual(hashlib.sha256(other.read_bytes()).hexdigest(), other_before)
                self.assertEqual(hashlib.sha256(selected.read_bytes()).hexdigest(), before)

    def test_database_selection_is_required_and_legacy_aliases_are_rejected(self):
        legacy = Path(__file__).parents[1] / 'signal.db'
        before = hashlib.sha256(legacy.read_bytes()).hexdigest() if legacy.exists() else None
        with patch.object(database, 'DB_PATH', None), patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'SIGNAL_F2_DB'):
                database.init_db()
            for selection in [str(legacy), 'relative.db']:
                with patch.dict(os.environ, {'SIGNAL_F2_DB': selection}):
                    with self.assertRaises(ValueError):
                        database.init_db()
            # Trusted test injection must never bypass protection of the actual legacy file.
            with patch.object(database, 'DB_PATH', legacy):
                with self.assertRaises(ValueError):
                    database.init_db()
            with tempfile.TemporaryDirectory() as directory:
                protected = Path(directory) / 'legacy.db'
                protected.write_bytes(b'protected legacy bytes')
                with patch.object(database, 'LEGACY_DB_PATH', protected):
                    alias = Path(directory) / 'alias.db'
                    alias.symlink_to(protected)
                    with patch.dict(os.environ, {'SIGNAL_F2_DB': str(alias)}):
                        with self.assertRaises(ValueError):
                            database.init_db()
                    with patch.object(database, 'DB_PATH', alias):
                        with self.assertRaises(ValueError):
                            database.init_db()
                    alias.unlink()
                    os.link(protected, alias)
                    with patch.dict(os.environ, {'SIGNAL_F2_DB': str(alias)}):
                        with self.assertRaises(ValueError):
                            database.init_db()
                    with patch.object(database, 'DB_PATH', alias):
                        with self.assertRaises(ValueError):
                            database.init_db()
        if before is not None:
            self.assertEqual(hashlib.sha256(legacy.read_bytes()).hexdigest(), before)

    def test_explicit_database_initializes_idempotently_and_preserves_migration_compatibility(self):
        with tempfile.TemporaryDirectory() as directory:
            selected = Path(directory) / 'f2.db'
            with sqlite3.connect(selected) as conn:
                conn.executescript('''
                    CREATE TABLE companies (id TEXT PRIMARY KEY, name TEXT NOT NULL, sector TEXT);
                    INSERT INTO companies VALUES ('NMBS', 'Nimbus Software', 'Software');
                    CREATE TABLE disclosures (id TEXT PRIMARY KEY, asset TEXT);
                    INSERT INTO disclosures VALUES ('old', 'unchanged source value');
                ''')
            with patch.object(database, 'DB_PATH', selected):
                database.init_db()
                database.init_db()
                with database.get_connection() as conn:
                    self.assertEqual(conn.execute('PRAGMA quick_check').fetchone()[0], 'ok')
                    self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
                    self.assertEqual(conn.execute('SELECT asset FROM disclosures').fetchone()[0], 'unchanged source value')
                    self.assertEqual(conn.execute("SELECT population FROM companies WHERE id = 'NMBS'").fetchone()[0], 'demo')
                    self.assertEqual(conn.execute('SELECT count(*) FROM disclosure_artifacts').fetchone()[0], 0)

    def test_local_legacy_database_migrates_only_on_a_temporary_copy(self):
        legacy = Path(__file__).parents[1] / 'signal.db'
        if not legacy.exists():
            self.skipTest('No local legacy database; constructed legacy migration is covered separately.')
        before = hashlib.sha256(legacy.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            copy = Path(directory) / 'legacy-copy.db'
            with sqlite3.connect(legacy.resolve().as_uri() + '?mode=ro', uri=True) as source, sqlite3.connect(copy) as target:
                source.backup(target)
                originals = {}
                for table in ['companies', 'price_points', 'news_items', 'discussion_items', 'findings', 'disclosures']:
                    columns = [row[1] for row in source.execute(f'PRAGMA table_info({table})')]
                    if columns:
                        # Compare original values by digest, without logging personal/source rows.
                        query = 'SELECT ' + ','.join('"' + column + '"' for column in columns) + ' FROM ' + table + ' ORDER BY id'
                        originals[query] = hashlib.sha256(repr(source.execute(query).fetchall()).encode()).hexdigest()
            with patch.object(database, 'DB_PATH', copy):
                database.init_db()
                database.init_db()
                with database.get_connection() as conn:
                    self.assertEqual(conn.execute('PRAGMA quick_check').fetchone()[0], 'ok')
                    self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
                    for query, expected in originals.items():
                        actual = hashlib.sha256(repr([tuple(row) for row in conn.execute(query)]).encode()).hexdigest()
                        self.assertEqual(actual, expected)
                    for table in ['disclosure_artifacts', 'event_evidence_assertions', 'watch_events', 'investigation_runs']:
                        self.assertEqual(conn.execute(f'SELECT count(*) FROM {table}').fetchone()[0], 0)
        self.assertEqual(hashlib.sha256(legacy.read_bytes()).hexdigest(), before)


class F2LocalApiTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.selection = patch.object(database, 'DB_PATH', Path(self.directory.name) / 'f2.db')
        self.selection.start()
        database.init_db()
        self.client = TestClient(app, base_url='http://localhost:8000', client=('127.0.0.1', 50000))

    def tearDown(self):
        self.client.close()
        self.selection.stop()
        self.directory.cleanup()

    def test_local_json_mutations_work_but_cross_site_and_nonlocal_requests_are_blocked(self):
        path = '/api/disclosures/house/filings/2021/20018021/retrievals'
        with patch('urllib.request.urlopen', side_effect=AssertionError('network forbidden')):
            for origin in ['https://untrusted.example', 'null', 'http://localhost:9999']:
                self.assertEqual(self.client.post(path, json={'purpose': 'manual'}, headers={'Origin': origin}).status_code, 403)
            self.assertEqual(self.client.post(path, data={'purpose': 'manual'}).status_code, 403)
            self.assertEqual(self.client.post(path, json={'purpose': 'manual'}, headers={'Sec-Fetch-Site': 'cross-site'}).status_code, 403)
            for origin in [None, 'http://localhost:5173', 'http://127.0.0.1:5173']:
                headers = {'Origin': origin} if origin else {}
                if origin:
                    # Embedded browsers may report cross-site even for an explicitly
                    # allowed loopback Origin. Origin remains the decisive boundary.
                    headers['Sec-Fetch-Site'] = 'cross-site'
                response = self.client.post(path, json={'purpose': 'manual'}, headers=headers)
                self.assertEqual(response.status_code, 409, response.text)
                self.assertEqual(response.json()['detail']['reasonCode'], 'house_live_access_unresolved')
            self.assertEqual(self.client.post('/api/disclosures/house/indexes/2021/retrievals', json={'purpose': 'manual'}).status_code, 409)
        for host in ['untrusted.example', 'evil@localhost', 'localhost/path', 'localhost:invalid']:
            self.assertEqual(self.client.get('/api/capabilities', headers={'Host': host}).status_code, 403)
        remote = TestClient(app, base_url='http://localhost:8000', client=('192.0.2.10', 50000))
        try:
            self.assertEqual(remote.get('/api/capabilities').status_code, 403)
        finally:
            remote.close()

    def test_startup_without_network_preserves_capability_gates_and_watch_recovery(self):
        with patch('urllib.request.urlopen', side_effect=AssertionError('network forbidden')):
            with TestClient(app, base_url='http://localhost:8000', client=('127.0.0.1', 50001)) as client:
                response = client.get('/api/capabilities')
                self.assertEqual(response.status_code, 200, response.text)
                capabilities = {item['id']: item for item in response.json()['capabilities']}
                self.assertEqual(capabilities['market.outcomes']['availability'], 'unavailable')
                self.assertEqual(capabilities['monitoring.market_checks']['availability'], 'unavailable')
                self.assertEqual(client.get('/api/watch-events').json()['watchEvents'], [])

    def test_offline_official_sample_is_inspectable_and_never_becomes_real_evidence(self):
        expected_hash = '071aab65d8223132ac372501605fadc98948e3c8f0faa006931ea3902c86d7c2'
        with patch('urllib.request.urlopen', side_effect=AssertionError('network forbidden')):
            initial = self.client.get('/api/disclosures/offline-sample')
            self.assertEqual(initial.status_code, 200, initial.text)
            self.assertEqual(initial.json()['evidence']['artifacts'], [])
            first = self.client.post('/api/disclosures/offline-sample/observations', json={})
            self.assertEqual(first.status_code, 201, first.text)
            second = self.client.post('/api/disclosures/offline-sample/observations', json={})
            self.assertEqual(second.status_code, 201, second.text)
            self.assertEqual(first.json()['artifactVersionId'], second.json()['artifactVersionId'])
            response = self.client.get('/api/disclosures/offline-sample').json()
            self.assertEqual(response['population'], 'test')
            self.assertFalse(response['liveAcquisitionPermitted'])
            artifact = response['evidence']['artifacts'][0]
            self.assertEqual(len(artifact['versions']), 1)
            version = artifact['versions'][0]
            self.assertEqual(version['contentSha256'], expected_hash)
            self.assertEqual(len(version['rowOccurrences']), 1)
            self.assertEqual(version['rowOccurrences'][0]['rawFields']['asset'], 'Dominion Energy, Inc. (D) [ST]')
            self.assertEqual(len(artifact['retrievalObservations']), 2)
            for observation in artifact['retrievalObservations']:
                self.assertIsNone(observation['httpStatus'])
                self.assertEqual(observation['sourceMetadata']['observationKind'], 'offline_sample_read')
                self.assertIsNone(observation['sourceMetadata']['originalRetrievedAt'])
            path = f"/api/disclosures/offline-sample/artifacts/{artifact['id']}/versions/{version['id']}/content"
            content = self.client.get(path)
            self.assertEqual(content.status_code, 200, content.text[:100] if content.status_code != 200 else '')
            self.assertEqual(hashlib.sha256(content.content).hexdigest(), expected_hash)
            self.assertEqual(content.headers['content-type'], 'application/pdf')
            self.assertIn('attachment', content.headers['content-disposition'])
            self.assertEqual(self.client.get('/api/disclosures/evidence').json()['artifacts'], [])
            self.assertEqual(self.client.get('/api/events', params={
                'perspective': 'system_observation', 'asOf': int(time.time() * 1000),
            }).json()['events'], [])
            self.assertEqual(self.client.get('/api/watch-events').json()['watchEvents'], [])
            self.assertEqual(self.client.get('/api/findings').json()['findings'], [])
            real_path = f"/api/disclosures/artifacts/{artifact['id']}/versions/{version['id']}"
            self.assertEqual(self.client.get(real_path).status_code, 404)
            self.assertEqual(self.client.get(path.replace(version['id'], 'unknown')).status_code, 404)
            self.assertEqual(self.client.post('/api/disclosures/offline-sample/observations', json={'population': 'real'}).status_code, 422)

    def test_missing_or_changed_local_sample_does_not_create_evidence(self):
        from routers import disclosures

        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / 'sample.pdf'
            with patch.object(disclosures, 'OFFLINE_SAMPLE', changed):
                self.assertEqual(self.client.post('/api/disclosures/offline-sample/observations', json={}).status_code, 503)
                changed.write_bytes(b'%PDF changed sample')
                self.assertEqual(self.client.post('/api/disclosures/offline-sample/observations', json={}).status_code, 409)
                self.assertEqual(self.client.get('/api/disclosures/offline-sample').json()['evidence']['artifacts'], [])
                self.assertEqual(self.client.get('/api/disclosures/evidence').json()['artifacts'], [])
