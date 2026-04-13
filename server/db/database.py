import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

DB_PATH = Path(__file__).parent.parent / "signal.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

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
        conn.executemany(
            "INSERT OR IGNORE INTO companies (id, name, sector) VALUES (?, ?, ?)",
            SEED_COMPANIES,
        )
