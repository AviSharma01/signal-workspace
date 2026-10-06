import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

DB_PATH = Path(__file__).parent.parent / "signal.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Exact identities of the fixtures written by the legacy seed_demo.py.
LEGACY_DEMO_COMPANIES = {
    "NMBS": "Nimbus Software",
    "ORCH": "Orchid Biosciences",
    "HLIX": "Helix Therapeutics",
    "VRTA": "Vertica Biotech",
    "DRFT": "Drift Dynamics",
}

SEED_COMPANIES: list[tuple[str, str, str]] = [
    ("AAPL", "Apple", "Technology"),
    ("MSFT", "Microsoft", "Technology"),
    ("GOOGL", "Alphabet", "Technology"),
    ("AMZN", "Amazon", "Consumer"),
    ("NVDA", "Nvidia", "Semiconductors"),
]


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    schema = SCHEMA_PATH.read_text()
    with get_connection() as conn:
        conn.executescript(schema)
        _isolate_legacy_context(conn)
        conn.executemany(
            "INSERT OR IGNORE INTO companies (id, name, sector) VALUES (?, ?, ?)",
            SEED_COMPANIES,
        )


def _isolate_legacy_context(conn: sqlite3.Connection) -> None:
    """Upgrade old context tables and quarantine known fixtures without rewriting raw data."""
    for table in ("companies", "news_items", "discussion_items"):
        columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})")}
        if "population" not in columns:
            conn.execute(
                f"ALTER TABLE {table} ADD COLUMN population TEXT NOT NULL DEFAULT 'real' "
                "CHECK (population IN ('real', 'demo', 'test', 'evaluation'))"
            )
    conn.executemany(
        "UPDATE companies SET population = 'demo' WHERE id = ? AND name = ? AND population = 'real'",
        LEGACY_DEMO_COMPANIES.items(),
    )
    conn.execute(
        "UPDATE news_items SET population = 'demo' WHERE population = 'real' AND "
        "(id IN ('seed-news-nmbs-001', 'seed-news-orch-001') OR source = 'DemoWire' OR "
        "company_id IN (SELECT id FROM companies WHERE population = 'demo'))"
    )
    conn.execute(
        "UPDATE discussion_items SET population = 'demo' WHERE population = 'real' AND "
        "(source = 'DemoWire' OR company_id IN (SELECT id FROM companies WHERE population = 'demo'))"
    )
