from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from jobs.scheduler import start_scheduler, shutdown_scheduler
from routers import analysis, capabilities, companies, disclosures, events, findings, prices, scan, signals, watch_events


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Accept", "Content-Type"],
)

app.include_router(companies.router)
app.include_router(capabilities.router)
app.include_router(signals.router)
app.include_router(prices.router)
app.include_router(findings.router)
app.include_router(scan.router)
app.include_router(disclosures.router)
app.include_router(events.router)
app.include_router(watch_events.router)
app.include_router(analysis.router)
