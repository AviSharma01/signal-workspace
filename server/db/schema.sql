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