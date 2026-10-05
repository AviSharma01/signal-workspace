import unittest
from datetime import UTC, datetime
from unittest.mock import patch

from jobs import scheduler
from jobs.watch_events import schedule_watch_expiry, run_startup_watch_recovery, run_watch_expiry
from tests import test_watch_events


class RecordingScheduler:
    running = True

    def __init__(self):
        self.jobs = {}

    def add_job(self, function, trigger, **options):
        self.jobs[options["id"]] = (function, trigger, options)

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def remove_job(self, job_id):
        self.jobs.pop(job_id)


class WatchJobsTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_watch_events.WatchApplicationTest()
        self.fixture.setUp()
        self.fixture.fixture.population = "real"
        self.scheduler = RecordingScheduler()
        self.patch = patch.object(scheduler, "_scheduler", self.scheduler)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.fixture.tearDown()

    def admit(self):
        data = self.fixture.fixture
        version, rows = data.official()
        data.identities(version, rows[0]["id"], data.now)
        return self.fixture.watch.admit(f"event:{rows[0]['id']}", population="real")

    def test_expiry_job_is_rebuilt_from_persisted_boundary_and_records_at_actual_execution_time(self):
        admitted = self.admit()
        boundary = admitted["currentEvaluation"]["expirySupport"]["expiresAt"]
        schedule_watch_expiry(application=self.fixture.watch)
        function, trigger, options = self.scheduler.jobs["watch-known-expiry"]
        self.assertEqual(trigger, "date")
        self.assertEqual(options["run_date"], datetime.fromtimestamp(boundary / 1000, UTC))
        self.assertTrue(options["replace_existing"])
        self.fixture.fixture.now = boundary + 10_000
        self.assertEqual(function(application=self.fixture.watch), 1)
        result = self.fixture.watch.get(admitted["watchEvent"]["id"], population="real")
        self.assertEqual(result["lifecycleHistory"][-1]["evaluatedAt"], boundary + 10_000)
        self.assertNotIn("watch-known-expiry", self.scheduler.jobs)
        self.assertEqual(run_watch_expiry(application=self.fixture.watch), 0)

    def test_startup_recovers_overdue_assessment_once_without_backdating(self):
        admitted = self.admit()
        boundary = admitted["currentEvaluation"]["expirySupport"]["expiresAt"]
        self.fixture.fixture.now = boundary + 86_400_000
        self.assertEqual(run_startup_watch_recovery(application=self.fixture.watch), 1)
        self.assertEqual(run_startup_watch_recovery(application=self.fixture.watch), 0)
        result = self.fixture.watch.get(admitted["watchEvent"]["id"], population="real")
        self.assertEqual(result["lifecycleHistory"][-1]["trigger"], "startup_recovery")
        self.assertEqual(result["lifecycleHistory"][-1]["evaluatedAt"], boundary + 86_400_000)


if __name__ == "__main__":
    unittest.main()
