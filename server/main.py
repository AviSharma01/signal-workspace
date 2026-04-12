from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db.database import init_db
from jobs.scheduler import start_scheduler, shutdown_scheduler
from routers import companies, signals, prices


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
    allow_methods=["GET"],
    allow_headers=["Accept", "Content-Type"],
)

app.include_router(companies.router)
app.include_router(signals.router)
app.include_router(prices.router)
