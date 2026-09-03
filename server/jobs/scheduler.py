from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from jobs.prices import fetch_prices
from jobs.news import fetch_news
from jobs.discussion import fetch_discussion
_scheduler = BackgroundScheduler()


def start_scheduler() -> None:
    now = datetime.now()
    _scheduler.add_job(fetch_prices, "interval", minutes=15, next_run_time=now)
    _scheduler.add_job(fetch_news, "interval", minutes=30, next_run_time=now)
    _scheduler.add_job(fetch_discussion, "interval", minutes=60, next_run_time=now)
    _scheduler.start()


def shutdown_scheduler() -> None:
    _scheduler.shutdown(wait=False)
