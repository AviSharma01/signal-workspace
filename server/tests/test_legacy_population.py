"""Legacy context populations stay isolated, including previously seeded databases."""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from db import database
from routers import companies, signals
import seed_demo


class LegacyPopulationTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / 'legacy.db'
        self.db_patch = patch.object(database, 'DB_PATH', self.db_path)
        self.db_patch.start()
        database.init_db()
        api = FastAPI()
        api.include_router(companies.router)
        api.include_router(signals.router)
        self.client = TestClient(api)

    def tearDown(self):
        self.client.close()
        self.db_patch.stop()
        self.temp.cleanup()

    def seed(self):
        with redirect_stdout(io.StringIO()):
            seed_demo.seed(demo=True)

    def test_seeding_requires_explicit_opt_in_and_default_db_stays_clean(self):
        with self.assertRaisesRegex(ValueError, 'explicit_demo_opt_in_required'):
            with redirect_stdout(io.StringIO()):
                seed_demo.seed()
        with database.get_connection() as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM news_items').fetchone()[0], 0)
            self.assertEqual(conn.execute('SELECT count(*) FROM companies').fetchone()[0], 5)

    def test_default_queries_exclude_fixtures_and_explicit_demo_queries_retain_them(self):
        self.seed()
        self.seed()  # Explicit demo workflow remains idempotent.
        ids = {row['id'] for row in self.client.get('/api/companies').json()}
        self.assertTrue(ids.isdisjoint(seed_demo.DEMO_TICKERS))
        self.assertIn('AAPL', ids)
        self.assertEqual(self.client.get('/api/signals/NMBS').status_code, 404)
        demo = self.client.get('/api/companies', params={'population': 'demo'})
        self.assertEqual(demo.status_code, 200, demo.text)
        self.assertEqual({row['id'] for row in demo.json()}, set(seed_demo.DEMO_TICKERS))
        news = self.client.get('/api/signals/NMBS', params={'population': 'demo'})
        self.assertEqual(news.status_code, 200, news.text)
        self.assertEqual(news.json()['news'][0]['id'], 'seed-news-nmbs-001')
        # A stale label cannot choose a data population for default queries.
        self.assertEqual(self.client.get('/api/signals/NMBS', params={
            'classification': 'legacy_v1_context'}).status_code, 404)
        self.assertEqual(self.client.get('/api/signals/AAPL', params={
            'population': 'demo'}).status_code, 404)

    def test_company_and_context_population_filters_exclude_test_and_evaluation(self):
        with database.get_connection() as conn:
            for population in ['real', 'demo', 'test', 'evaluation']:
                conn.execute('INSERT INTO companies (id, name, population) VALUES (?, ?, ?)',
                             (population.upper(), population, population))
                conn.execute('INSERT INTO news_items (id, company_id, headline, population) VALUES (?, ?, ?, ?)',
                             (population, 'AAPL', 'legacy_v1_context', population))
                conn.execute('INSERT INTO discussion_items (id, company_id, title, population) VALUES (?, ?, ?, ?)',
                             (population, 'AAPL', 'legacy_v1_context', population))
        ids = {row['id'] for row in self.client.get('/api/companies').json()}
        self.assertIn('REAL', ids)
        self.assertTrue(ids.isdisjoint({'DEMO', 'TEST', 'EVALUATION'}))
        payload = self.client.get('/api/signals/AAPL').json()
        self.assertEqual(payload['classification'], 'legacy_v1_context')
        for kind in ['news', 'discussion']:
            self.assertEqual([row['id'] for row in payload[kind]], ['real'])
        for population in ['test', 'evaluation', 'anything']:
            for route in ['/api/companies', '/api/signals/AAPL']:
                self.assertEqual(self.client.get(route, params={'population': population}).status_code, 422)

    def test_old_schema_demo_rows_are_quarantined_without_changing_source_values(self):
        # Reproduce the old schema, where CREATE IF NOT EXISTS alone cannot add populations.
        old_db = Path(self.temp.name) / 'pre-patch.db'
        with patch.object(database, 'DB_PATH', old_db):
            with database.get_connection() as conn:
                conn.executescript('''
                    CREATE TABLE companies (id TEXT PRIMARY KEY, name TEXT NOT NULL, sector TEXT);
                    CREATE TABLE news_items (id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                        headline TEXT NOT NULL, summary TEXT, source TEXT, url TEXT, published_at INTEGER);
                    CREATE TABLE discussion_items (id TEXT PRIMARY KEY, company_id TEXT NOT NULL,
                        title TEXT NOT NULL, summary TEXT, source TEXT, url TEXT, published_at INTEGER);
                    INSERT INTO companies VALUES ('NMBS', 'Nimbus Software', 'Software');
                    INSERT INTO companies VALUES ('AAPL', 'Apple', 'Technology');
                    INSERT INTO news_items VALUES ('seed-news-nmbs-001', 'NMBS', 'raw demo headline',
                        'raw summary', 'DemoWire', 'https://example.com/demo', 123);
                    INSERT INTO news_items VALUES ('old-demo-on-real', 'AAPL', 'legacy_v1_context',
                        NULL, 'DemoWire', NULL, 123);
                    INSERT INTO discussion_items VALUES ('old-demo-discussion', 'NMBS', 'raw demo title',
                        NULL, 'Reddit', NULL, 123);
                    INSERT INTO news_items VALUES ('real-news', 'AAPL', 'real headline',
                        NULL, 'RealWire', NULL, 123);
                ''')
            database.init_db()
            database.init_db()  # Startup migration is idempotent.
            ids = {row['id'] for row in self.client.get('/api/companies').json()}
            self.assertNotIn('NMBS', ids)
            self.assertEqual(self.client.get('/api/signals/NMBS').status_code, 404)
            self.assertEqual([row['id'] for row in self.client.get('/api/signals/AAPL').json()['news']], ['real-news'])
            payload = self.client.get('/api/signals/NMBS', params={'population': 'demo'}).json()
            self.assertEqual(payload['news'][0]['headline'], 'raw demo headline')
            self.assertEqual(payload['news'][0]['summary'], 'raw summary')
            self.assertEqual(payload['discussion'][0]['title'], 'raw demo title')
            with database.get_connection() as conn:
                row = conn.execute("SELECT * FROM news_items WHERE id = 'seed-news-nmbs-001'").fetchone()
                self.assertEqual(row['population'], 'demo')
                self.assertEqual(row['published_at'], 123)

    def test_demo_seed_cannot_overwrite_non_demo_data(self):
        with database.get_connection() as conn:
            conn.execute("INSERT INTO companies (id, name) VALUES ('NMBS', 'Real issuer')")
        with self.assertRaisesRegex(ValueError, 'demo_company_population_conflict'):
            self.seed()
        with database.get_connection() as conn:
            self.assertEqual(conn.execute("SELECT name FROM companies WHERE id = 'NMBS'").fetchone()[0], 'Real issuer')
            self.assertEqual(conn.execute('SELECT count(*) FROM news_items').fetchone()[0], 0)
