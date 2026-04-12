import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "signal.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"

SEED_COMPANIES: list[tuple[str, str, str]] = [
    ("AAPL", "Apple", "Technology"),
    ("MSFT", "Microsoft", "Technology"),
    ("GOOGL", "Alphabet", "Technology"),
    ("AMZN", "Amazon", "Consumer"),
    ("NVDA", "Nvidia", "Semiconductors"),
]


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    schema = SCHEMA_PATH.read_text()
    with get_connection() as conn:
        conn.executescript(schema)
        conn.executemany(
            "INSERT OR IGNORE INTO companies (id, name, sector) VALUES (?, ?, ?)",
            SEED_COMPANIES,
        )
