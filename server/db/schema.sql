CREATE TABLE IF NOT EXISTS companies (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  sector TEXT
);

CREATE TABLE IF NOT EXISTS price_points (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  company_id TEXT NOT NULL,
  timestamp INTEGER NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume INTEGER,
  FOREIGN KEY (company_id) REFERENCES companies(id),
  UNIQUE (company_id, timestamp)
);

CREATE TABLE IF NOT EXISTS news_items (
  id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL,
  headline TEXT NOT NULL,
  summary TEXT,
  source TEXT,
  url TEXT,
  published_at INTEGER,
  FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS discussion_items (
  id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT,
  source TEXT,
  url TEXT,
  published_at INTEGER,
  FOREIGN KEY (company_id) REFERENCES companies(id)
);

CREATE TABLE IF NOT EXISTS findings (
    id              TEXT PRIMARY KEY,           -- uuid4
    company_id      TEXT NOT NULL,              -- ticker; FK to companies.id
    created_at      INTEGER NOT NULL,           -- Unix ms
    trigger_json    TEXT NOT NULL,              -- serialized trigger dict
    primary_driver  TEXT NOT NULL,              -- news | discussion | sector | unexplained
    hypothesis      TEXT NOT NULL,
    evidence_json   TEXT NOT NULL,              -- serialized evidence list
    confidence      TEXT NOT NULL,              -- high | medium | low
    needs_human_review INTEGER NOT NULL,        -- 0 or 1 (SQLite has no bool)
    iterations      INTEGER NOT NULL,
    cost_usd        REAL NOT NULL,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
CREATE INDEX IF NOT EXISTS idx_findings_company_created
    ON findings(company_id, created_at DESC);