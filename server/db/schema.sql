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

CREATE TABLE IF NOT EXISTS disclosure_source_filings (
    id TEXT PRIMARY KEY,
    population TEXT NOT NULL CHECK (population IN ('real', 'demo', 'test', 'evaluation')),
    source_name TEXT NOT NULL,
    source_filing_id TEXT NOT NULL,
    chamber TEXT NOT NULL CHECK (chamber IN ('house', 'senate', 'unknown')),
    source_url TEXT,
    discovered_at INTEGER NOT NULL,
    raw_metadata_json TEXT NOT NULL,
    UNIQUE (population, source_name, source_filing_id)
);

CREATE TABLE IF NOT EXISTS disclosure_artifacts (
    id TEXT PRIMARY KEY,
    population TEXT NOT NULL CHECK (population IN ('real', 'demo', 'test', 'evaluation')),
    source_name TEXT NOT NULL,
    source_authority TEXT NOT NULL CHECK (source_authority IN ('official', 'supporting')),
    artifact_kind TEXT NOT NULL,
    source_filing_record_id TEXT,
    source_url TEXT NOT NULL,
    media_type TEXT NOT NULL,
    created_at INTEGER NOT NULL,
    FOREIGN KEY (source_filing_record_id) REFERENCES disclosure_source_filings(id),
    UNIQUE (population, source_name, artifact_kind, source_url)
);

CREATE TABLE IF NOT EXISTS disclosure_artifact_versions (
    id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    content_sha256 TEXT NOT NULL,
    raw_content BLOB NOT NULL,
    content_length INTEGER NOT NULL,
    media_type TEXT NOT NULL,
    first_observed_at INTEGER NOT NULL,
    FOREIGN KEY (artifact_id) REFERENCES disclosure_artifacts(id),
    UNIQUE (artifact_id, content_sha256)
);

CREATE TABLE IF NOT EXISTS disclosure_retrieval_observations (
    id TEXT PRIMARY KEY,
    artifact_id TEXT NOT NULL,
    artifact_version_id TEXT,
    observed_at INTEGER NOT NULL,
    purpose TEXT NOT NULL CHECK (purpose IN ('daily_discovery', 'startup_catch_up', 'reconciliation', 'manual')),
    availability_status TEXT NOT NULL CHECK (availability_status IN ('available', 'unavailable', 'unknown')),
    freshness_status TEXT NOT NULL CHECK (freshness_status IN ('current', 'stale', 'unknown')),
    coverage_status TEXT NOT NULL CHECK (coverage_status IN ('complete', 'partial', 'unknown')),
    http_status INTEGER,
    source_metadata_json TEXT NOT NULL,
    FOREIGN KEY (artifact_id) REFERENCES disclosure_artifacts(id),
    FOREIGN KEY (artifact_version_id) REFERENCES disclosure_artifact_versions(id)
);

CREATE TABLE IF NOT EXISTS disclosure_extractions (
    id TEXT PRIMARY KEY,
    artifact_version_id TEXT NOT NULL,
    method TEXT NOT NULL,
    method_version TEXT NOT NULL,
    extracted_at INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('succeeded', 'partial', 'failed', 'unsupported')),
    representation_json TEXT,
    error TEXT,
    FOREIGN KEY (artifact_version_id) REFERENCES disclosure_artifact_versions(id),
    UNIQUE (artifact_version_id, method, method_version)
);

CREATE TABLE IF NOT EXISTS disclosure_row_occurrences (
    id TEXT PRIMARY KEY,
    artifact_version_id TEXT NOT NULL,
    source_filing_record_id TEXT,
    ordinal INTEGER NOT NULL,
    raw_fields_json TEXT NOT NULL,
    parse_status TEXT NOT NULL,
    FOREIGN KEY (artifact_version_id) REFERENCES disclosure_artifact_versions(id),
    FOREIGN KEY (source_filing_record_id) REFERENCES disclosure_source_filings(id),
    UNIQUE (artifact_version_id, ordinal)
);

CREATE TABLE IF NOT EXISTS disclosure_normalizations (
    id TEXT PRIMARY KEY,
    row_occurrence_id TEXT NOT NULL,
    extraction_id TEXT NOT NULL,
    method TEXT NOT NULL,
    method_version TEXT NOT NULL,
    normalized_at INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('succeeded', 'partial', 'failed')),
    normalized_fields_json TEXT NOT NULL,
    issues_json TEXT NOT NULL,
    FOREIGN KEY (row_occurrence_id) REFERENCES disclosure_row_occurrences(id),
    FOREIGN KEY (extraction_id) REFERENCES disclosure_extractions(id),
    UNIQUE (row_occurrence_id, method, method_version)
);

CREATE TABLE IF NOT EXISTS disclosure_source_filing_evidence (
    id TEXT PRIMARY KEY,
    source_filing_record_id TEXT NOT NULL,
    artifact_version_id TEXT NOT NULL,
    extraction_id TEXT NOT NULL,
    source_record_key TEXT NOT NULL,
    observed_at INTEGER NOT NULL,
    FOREIGN KEY (source_filing_record_id) REFERENCES disclosure_source_filings(id),
    FOREIGN KEY (artifact_version_id) REFERENCES disclosure_artifact_versions(id),
    FOREIGN KEY (extraction_id) REFERENCES disclosure_extractions(id),
    UNIQUE (source_filing_record_id, artifact_version_id, extraction_id, source_record_key)
);

CREATE INDEX IF NOT EXISTS idx_disclosure_artifacts_population
    ON disclosure_artifacts(population, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_disclosure_observations_artifact
    ON disclosure_retrieval_observations(artifact_id, observed_at);
CREATE INDEX IF NOT EXISTS idx_disclosure_rows_version
    ON disclosure_row_occurrences(artifact_version_id, ordinal);
CREATE INDEX IF NOT EXISTS idx_disclosure_normalizations_row
    ON disclosure_normalizations(row_occurrence_id, normalized_at);
CREATE INDEX IF NOT EXISTS idx_disclosure_filing_evidence_filing
    ON disclosure_source_filing_evidence(source_filing_record_id, observed_at);
