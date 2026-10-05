from datetime import UTC, datetime

from db.database import get_connection
from watch_events import WatchApplication


_application = WatchApplication(get_connection)


def schedule_watch_expiry(*, application: WatchApplication = _application) -> None:
    from jobs.scheduler import _scheduler

    # The normal production scheduler owns one replaceable date job, without a
    # queue or persisted scheduler state. Startup reconstructs it from history.
    if not _scheduler.running:
        return
    boundary = application.next_evaluation_at(population="real")
    if boundary is None:
        if _scheduler.get_job("watch-known-expiry") is not None:
            _scheduler.remove_job("watch-known-expiry")
        return
    _scheduler.add_job(
        run_watch_expiry, "date", run_date=datetime.fromtimestamp(boundary / 1000, UTC),
        id="watch-known-expiry", replace_existing=True, misfire_grace_time=None,
    )


def run_watch_expiry(*, application: WatchApplication = _application) -> int:
    changed = application.reevaluate_due(population="real")
    schedule_watch_expiry(application=application)
    return changed


def run_startup_watch_recovery(*, application: WatchApplication = _application) -> int:
    changed = application.reevaluate_all(population="real", trigger="startup_recovery")
    schedule_watch_expiry(application=application)
    return changed


def run_watch_recovery_check(*, application: WatchApplication = _application) -> int:
    # Retry overdue boundaries or evidence committed before a failed assessment.
    # Unchanged recovery records nothing; startup/downtime never invent actions.
    changed = application.reevaluate_all(population="real", trigger="startup_recovery")
    schedule_watch_expiry(application=application)
    return changed
