from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from jobs.prices import fetch_prices
from jobs.news import fetch_news
from jobs.discussion import fetch_discussion
from jobs.disclosures import run_daily_disclosure_discovery, run_startup_disclosure_catch_up

_scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    now = datetime.now()
    _scheduler.add_job(fetch_prices, "interval", minutes=15, next_run_time=now)
    _scheduler.add_job(fetch_news, "interval", minutes=30, next_run_time=now)
    _scheduler.add_job(fetch_discussion, "interval", minutes=60, next_run_time=now)
    _scheduler.add_job(
        run_startup_disclosure_catch_up,
        "date",
        run_date=now,
        id="disclosure-startup-catch-up",
        replace_existing=True,
    )
    _scheduler.add_job(
        run_daily_disclosure_discovery,
        "cron",
        hour=3,
        minute=0,
        timezone="America/New_York",
        id="disclosure-daily-discovery",
        replace_existing=True,
    )
    _scheduler.start()


def shutdown_scheduler() -> None:
    _scheduler.shutdown(wait=False)
