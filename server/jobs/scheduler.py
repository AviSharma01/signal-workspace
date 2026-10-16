from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from jobs.watch_events import run_startup_watch_recovery, run_watch_recovery_check

_scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    now = datetime.now()
    # F2 Stage 1 is a bounded manual workflow. No external collection runs on
    # startup or in the background; persisted Watch recovery remains enabled.
    _scheduler.add_job(
        run_watch_recovery_check,
        "interval",
        minutes=1,
        id="watch-recovery-check",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.add_job(
        run_startup_watch_recovery,
        "date",
        run_date=now,
        id="watch-startup-recovery",
        replace_existing=True,
        misfire_grace_time=None,
    )
    _scheduler.start()


def shutdown_scheduler() -> None:
    _scheduler.shutdown(wait=False)
