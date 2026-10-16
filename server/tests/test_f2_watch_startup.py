"""Cold backend starts recover persisted synthetic Watches in a temporary DB only."""
import json
import subprocess
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tests import test_events
from watch_events import WatchApplication


# Each invocation is a new backend process. No recovery function or scheduler is
# replaced; completion is observed from the actual APScheduler startup job.
START_BACKEND = r'''
import json
import sys
import threading
from pathlib import Path
from unittest.mock import patch
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from fastapi.testclient import TestClient
from db import database

database.DB_PATH = Path(sys.argv[1])  # Isolated temporary test injection only.
from jobs import scheduler
from main import app

done = threading.Event()
failures = []
def completed(event):
    if event.job_id == 'watch-startup-recovery':
        if event.exception:
            failures.append(type(event.exception).__name__)
        done.set()
scheduler._scheduler.add_listener(completed, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
with patch('urllib.request.urlopen', side_effect=AssertionError('External retrieval forbidden')), \
     patch('socket.socket.connect', side_effect=AssertionError('External connection forbidden')):
    with TestClient(app, base_url='http://localhost:8000', client=('127.0.0.1', 50000)) as client:
        assert done.wait(5), 'Actual lifespan did not complete Watch startup recovery'
        assert not failures, failures
        response = client.get('/api/watch-events')
        assert response.status_code == 200, response.text
        jobs = scheduler._scheduler.get_jobs()
        assert {job.id for job in jobs} == {'watch-recovery-check', 'watch-known-expiry'}
        assert all(job.func.__module__ == 'jobs.watch_events' for job in jobs)
        watches = {}
        for detail in response.json()['watchEvents']:
            watch = detail['watchEvent']
            watches[watch['id']] = {
                'admittedAt': watch['admittedAt'],
                'active': detail['currentEvaluation']['activeEligibility']['eligible'],
                'recency': detail['lastPersistedAssessment']['recency']['status'],
                'history': [{'trigger': item['trigger'], 'evaluatedAt': item['evaluatedAt'],
                             'persistedAt': item['persistedAt'], 'reasons': item['transitionReasons']}
                            for item in detail['lifecycleHistory']],
            }
        expiry_job = scheduler._scheduler.get_job('watch-known-expiry')
        print(json.dumps({'watches': watches, 'nextExpiry': int(expiry_job.next_run_time.timestamp() * 1000)}))
'''


class F2WatchStartupTest(unittest.TestCase):
    def test_persisted_nonempty_watches_recover_through_lifespan_and_cold_backend_restart(self):
        fixture = test_events.EventApplicationTest()
        fixture.setUp()
        self.addCleanup(fixture.tearDown)
        fixture.population = 'real'  # Synthetic records confined to this temporary DB.
        now = datetime.now(UTC)
        fixture.now = int((now - timedelta(days=5)).timestamp() * 1000)
        watch = WatchApplication(fixture.connection, lambda: fixture.now)
        event_ids = []
        for age, document in [(34, '20030001'), (10, '20030002')]:
            publication = (now - timedelta(days=age)).isoformat()
            version, rows = fixture.official(publication, document=document, observed=test_events.ms(publication) + 1000)
            fixture.identities(version, rows[0]['id'], test_events.ms(publication))
            event_ids.append(f"event:{rows[0]['id']}")
        admitted = [watch.admit(event_id, population='real') for event_id in event_ids]
        old_id, active_id = [detail['watchEvent']['id'] for detail in admitted]
        self.assertTrue(all(detail['currentEvaluation']['activeEligibility']['eligible'] for detail in admitted))
        expiry = admitted[0]['currentEvaluation']['expirySupport']['expiresAt']
        future_expiry = admitted[1]['currentEvaluation']['expirySupport']['expiresAt']

        def restart():
            started_at = int(datetime.now(UTC).timestamp() * 1000)
            process = subprocess.run([sys.executable, '-B', '-c', START_BACKEND, str(fixture.path)],
                                     cwd=Path(__file__).parents[1], capture_output=True, text=True, timeout=20)
            self.assertEqual(process.returncode, 0, process.stderr)
            return started_at, json.loads(process.stdout), int(datetime.now(UTC).timestamp() * 1000)

        started, first, finished = restart()
        self.assertEqual(set(first['watches']), {old_id, active_id})
        expired = first['watches'][old_id]
        self.assertFalse(expired['active'])
        self.assertEqual(expired['recency'], 'expired')
        self.assertEqual(len(expired['history']), 2)
        transition = expired['history'][-1]
        self.assertEqual(transition['trigger'], 'startup_recovery')
        self.assertEqual(transition['reasons'], ['expired'])
        self.assertLess(expiry, started)
        self.assertLessEqual(started, transition['evaluatedAt'])
        self.assertLessEqual(transition['evaluatedAt'], transition['persistedAt'])
        self.assertLessEqual(transition['persistedAt'], finished)
        self.assertEqual(expired['admittedAt'], fixture.now)
        self.assertTrue(first['watches'][active_id]['active'])
        self.assertEqual(len(first['watches'][active_id]['history']), 1)
        self.assertEqual(first['nextExpiry'], future_expiry)

        _, second, _ = restart()
        self.assertEqual(second, first, 'Cold restart must preserve history and rebuild the same expiry without duplication')
