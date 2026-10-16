import os
import sqlite3
import stat
from contextlib import closing, contextmanager
from functools import lru_cache
from pathlib import Path
from typing import ContextManager, Generator

LEGACY_DB_PATH = Path(__file__).parent.parent / "signal.db"
LOCAL_DB_DIR = Path(__file__).resolve().parents[1] / ".local"
F2_APPLICATION_ID = 0x53494732  # SIG2; ownership, not a methodology/schema version.
# Tests may supply an isolated Path. Runtime selection is always explicit.
DB_PATH: Path | None = None
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


def _selected_path() -> Path:
    selection = DB_PATH if DB_PATH is not None else os.environ.get("SIGNAL_F2_DB", "")
    if not selection or not Path(selection).is_absolute():
        raise ValueError("SIGNAL_F2_DB must explicitly select an absolute isolated database path")
    selected = Path(selection)
    if ".." in selected.parts:
        raise ValueError("Database path traversal is not permitted")
    try:
        path = selected.resolve()
    except (OSError, RuntimeError) as exc:
        raise ValueError("Database path cannot be resolved safely") from exc
    if DB_PATH is None and (
        LOCAL_DB_DIR.resolve() != LOCAL_DB_DIR
        or path != selected or not path.is_relative_to(LOCAL_DB_DIR)
    ):
        raise ValueError("SIGNAL_F2_DB must select a canonical path inside server/.local/")
    if path == LEGACY_DB_PATH.resolve() or (
        path.exists() and LEGACY_DB_PATH.exists() and path.samefile(LEGACY_DB_PATH)
    ):
        raise ValueError("SIGNAL_F2_DB must not select the legacy server/signal.db or an alias")
    for candidate in (path, *(Path(str(path) + suffix) for suffix in ("-journal", "-wal", "-shm"))):
        if candidate.is_symlink() or (candidate.exists() and (
            not stat.S_ISREG(candidate.stat().st_mode) or candidate.stat().st_nlink != 1
        )):
            raise ValueError("Database files must be regular files without symlink or hard-link aliases")
    return path


def _schema_signature(conn: sqlite3.Connection) -> frozenset:
    return frozenset(conn.execute(
        "SELECT type, name, sql FROM sqlite_schema WHERE name NOT GLOB 'sqlite_*'"
    ).fetchall())


@lru_cache(maxsize=1)
def _stage_one_schema() -> frozenset:
    with closing(sqlite3.connect(":memory:")) as conn:
        conn.executescript(SCHEMA_PATH.read_text())
        return _schema_signature(conn)


def _recognize_f2(path: Path) -> None:
    # Immutable/read-only inspection cannot recover a journal or change an
    # unrelated DB. The local operator must stop other writers before migration.
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True)) as conn:
            owner = conn.execute("PRAGMA application_id").fetchone()[0]
            recognized = owner in {0, F2_APPLICATION_ID} and _schema_signature(conn) == _stage_one_schema()
    except sqlite3.DatabaseError as exc:
        raise ValueError("Existing database is not a recognized F2 database") from exc
    if not recognized:
        raise ValueError("Existing database is not a recognized F2 database; it was not migrated")


@contextmanager
def _connection(*, initialize: bool = False) -> Generator[sqlite3.Connection, None, None]:
    path = _selected_path()
    if DB_PATH is None:
        if path.exists():
            _recognize_f2(path)
        elif initialize:
            # Exclusive creation refuses a file that appeared after selection.
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(descriptor)
        else:
            raise ValueError("Initialize the selected F2 database before accessing it")
    conn = sqlite3.connect(path)
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


def get_connection() -> ContextManager[sqlite3.Connection]:
    return _connection()


def init_db() -> None:
    schema = SCHEMA_PATH.read_text()
    with _connection(initialize=True) as conn:
        conn.executescript(schema)
        _isolate_legacy_context(conn)
        conn.execute(f"PRAGMA application_id = {F2_APPLICATION_ID}")


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
