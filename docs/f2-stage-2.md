# F2 Stage 2: bounded offline House corpus and recovery

Scope: the project owner's 2026-10-16 approval extends the existing isolated
Stage 1 fallback to six already-retained PDFs. This approves a local test-only
workflow, not source licensing rights, distribution, real-population promotion,
live acquisition, House operational readiness, or market-data readiness under
#31. The accepted free-first ADR and approved V2 specification are unchanged.
Stages 3–5, identity resolution, Watch admission, OCR, market data and q remain
outside this change.

## Declared evidence

`server/offline_house.py` contains the fixed `f2-offline-house@1` manifest.
No supplied URL, path, payload, population, timestamp or processing version is
accepted by its commands. All writes use the existing V2 tables in population
`test`. Available entries are declarations, distinct from imported evidence.
A fresh database has six entries, zero imports, no extraction outcome beyond
`not_attempted`, unknown completeness, and zero observations/source filings.
GET/status checks do not import or process files.

| Filing | Bytes | Pages | Independently recorded row starts | Existing extraction outcome |
|---|---:|---:|---:|---|
| 2021/20018021 | 56,079 | 1 | 1 | succeeded |
| 2026/20034556 | 68,943 | 2 | 5 | succeeded |
| 2025/20030699 | 97,617 | 5 | 33 | succeeded |
| 2018/9113416 | 32,908 | 1 | unknown | unsupported scan |
| 2018/20010021 | 55,475 | 2 | 5 | succeeded |
| 2025/20030387 | 366,564 | 41 | 296 starts | partial; two unresolved continuations |

The existing [fixture manifest](../server/tests/fixtures/house_ptr/README.md)
owns the full hashes and recorded provenance. All six hashes were independently
remeasured and matched before implementation. Native paired-date-line counts
were independently rechecked against table-extractor results; the fixture notes
also record earlier representative visual checks. This is not an every-cell or
whole-House validation. The 2025/2026 locators originated in V1 records; the
2018/2021 locators came from official annual indexes. Original HTTP receipts and
exact original retrieval/publication instants are unavailable. The five native
PDFs report RC4 encryption and copy restrictions in PDF metadata despite readable
text; readability grants no rights. No decryption/OCR capability is added.

The corpus totals 677,586 source bytes, 52 pages and 340 extracted row starts.
Four succeeded documents contribute 44 rows. The scan has unknown transaction
count; the long document has two partial rows and two unresolved fragments on
pages 16/18. Neither fragments nor repeated equal values may be silently removed
or counted as additional transactions. No annual-index bytes were found locally;
historical research hashes do not substitute for replayable index artifacts.
No index recovery or index-to-filing reconciliation is claimed.

## Application operations and persistence

The existing V2 source-filing/artifact/version/observation/extraction/occurrence/
normalization/evidence-link tables remain authoritative. No schema, migration,
queue, persistent job framework, acquisition manifest or scheduler is added.

- `GET /api/disclosures/offline-corpus`: declarations and reconstructed processing
  status, scoped retained evidence, local file presence (not a successful read),
  extraction limitations and deterministic reconciliation receipts.
- `POST /api/disclosures/offline-corpus/{key}/observations` with `{}`: read only the
  declared regular fixture file, reject links/unsafe roots, bound the read by
  expected size, verify SHA-256 and length, then persist a local-read observation
  and process retained evidence. Each explicit successful read appends an actual
  observation; unchanged content creates no new version/rows/normalizations.
- `POST /api/disclosures/offline-corpus/{key}/resume` with `{}`: require existing
  scoped evidence, verify retained database bytes against both the manifest and
  stored identity/length, repair interrupted filing linkage, and resume committed
  processing. It does not read the fixture or add retrieval/read observations.
- `GET /api/disclosures/offline-corpus/artifacts/{artifact}/versions/{version}/content`:
  return only a declared, integrity-verified retained PDF, with no-store/nosniff
  and an application-generated filename.

Stage 1's one-file routes remain compatible. Its observations are recognized by
the corpus view without inventing a new read or changing their metadata. Public
real-population routes cannot select or retrieve the test corpus.

Raw bytes and observations commit before interpretation. Filing linkage,
extraction representation, occurrence materialization/evidence linkage, and
normalization have short, serialized write phases. PDF parsing runs outside the
write lock. Concurrent extraction inserts reuse the committed winning result;
row and normalization checks run within their write transactions. A database
lock timeout returns a structured retryable 503, not an unhandled database error.
Conflicting retained records return an explicit conflict rather than overwrite.

Processing status is reconstructed from committed records, including the
filing-evidence link even for zero-row unsupported/failed extraction. Pending
stages remain visible after a crash. Startup performs no corpus imports; after
restart, use **Resume processing** explicitly. Browser pending state is temporary,
not a persisted assertion that a worker is still running.

`finished` means the implemented processing stages committed. It does not mean
successful or complete extraction. Extraction status remains separately
`succeeded`, `partial`, `failed` or `unsupported`; before extraction it is
`not_attempted`. Completeness is `unknown`, `partial`, or
`matched_sample_expectation`. Matching this bounded independent row-start count
is not universal filing completeness or eligibility. Parser failures/unsupported
scans are retained terminal outcomes for this method; Resume does not silently
rerun or relabel the same method. An explicitly implemented later method would
require a separate versioned change.

Receipts contain manifest/hash identity, engine, extraction outcome, independent
row-start expectation and comparison, materialized/normalized/partial counts,
fragment count, integrity and processing status. Their reconciliation fingerprint
excludes UUIDs and actual instants; observation/extraction/normalization times
remain their recorded actual instants. Repeated reads preserve the fingerprint
when the evidence/processing result is unchanged. Repeated Resume preserves all
observations and existing derived IDs. No durable attempt counter, elapsed-time
ledger or successful record for pre-validation failure is invented.

## Failure and integrity behavior

Missing/unsafe/tampered local files fail before evidence or successful observation
creation. Status exposes local presence separately from retained evidence. A
missing local fixture does not invalidate a previously verified database copy;
Resume and retained download still work. Unexpected changed fixture bytes are
blocked by the pinned manifest and never silently adopted.

Corrupt database-retained bytes block Resume and download and surface an
integrity error. Existing evidence is not overwritten by reimport. Preserve a
failed database for diagnosis and use the Stage 1 backup/recovery procedure.
A later approved changed source artifact would use existing content-version
storage, preserve prior versions and establish neither amendment nor row
correspondence automatically. Changed-content behavior is exercised only in
isolated synthetic tests, not by altering these official samples.

Pre-validation errors appear in the response/current local status and create no
persistent attempt history. If a request fails after an earlier stage committed,
refresh status and Resume from that stage. A lost success response does not
require another local read. All local observations use `httpStatus: null`,
`offline_sample_read`, unknown original retrieval, unknown live availability,
freshness and coverage. No system observation is backdated to a filing/signature
or transaction date.

## Run and verify

Use the [Stage 1 database and loopback launch policy](f2-stage-1.md). For a new
review database, from the repository root create `server/.local`, then run the
backend from `server/` with:

```sh
SIGNAL_F2_DB="$PWD/.local/f2-stage2-review.sqlite3" ./venv/bin/python -B -m uvicorn main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Run the frontend from the root with:

```sh
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open `/disclosures`. Inspect one sample at a time, expand extraction limitations,
rows, local observations and the reconciliation receipt, and use exact retained
PDF links. Re-reading adds an observation; Resume does not. Reload/restart the
same explicitly selected database to verify persistence. Existing Stage 1
ownership, canonical-path/alias/sidecar protection and Watch recovery are retained.
No automatic legacy collectors or external acquisition run.

Backend verification (from `server/`):

```sh
PYTHONPATH=.:tests ./venv/bin/python -B -m unittest tests.test_offline_house
PYTHONPATH=.:tests ./venv/bin/python -B -m unittest discover -s tests -t .
```

Frontend/repository verification (from root):

```sh
npm run test:frontend
npm run lint
./node_modules/.bin/tsc -b --pretty false
npm run build
git diff --check
```

The recovery tests terminate separate OS processes before/after SQLite commits
for raw observation, extraction, rows and normalization, then use the real app
lifespan and API in a new process. A zero-row scan also covers interruption after
extraction before its filing-evidence link. Concurrent imports, concurrent
resumes and mixed attempts must converge. Negative tests cover missing/changed/
linked files, retained-byte corruption, retryable storage failure and synthetic
parse failure; synthetic records exist only in temporary test databases.

## Verification receipt — 2026-10-16

- Final full backend suite: **289 passed**, including ten new corpus tests.
  Commit-boundary interruption uses eight before/after process exits plus a
  separate zero-row scan crash/restart. The failed-zero-row case also verifies
  pending filing-evidence linkage before Resume.
- Frontend: **13 passed**. Lint, TypeScript, production build and
  `git diff --check` passed. The build retains the existing nonblocking
  large-chunk warning. The backend test client emits its existing dependency
  deprecation warning.
- Real browser and HTTP API used the explicit canonical
  `server/.local/f2-stage2-review.sqlite3`. Before import the browser showed
  zero imported of six declared samples. All six were then imported through
  browser controls: six versions, 340 rows/normalizations, four succeeded
  extractions, one unsupported scan with unknown completeness, and one partial
  extraction with two partial rows/two fragments.
- Browser inspection expanded the scan's `page_1:no_native_text` outcome and
  the long filing's page-16/page-18 continuation details. The exact retained
  2021 PDF was downloaded through the local application and matched 56,079 bytes
  and SHA-256 `071aab65d8223132ac372501605fadc98948e3c8f0faa006931ea3902c86d7c2`.
  No external source download occurred.
- Cold backend restarts, page reload and browser Resume preserved every
  artifact-version/row ID, observation count and reconciliation fingerprint.
  A deliberate browser read-again then increased only the first filing's
  observation count from one to two; final corpus total was seven observations.
  The unchanged fingerprints/IDs were checked against a pre-restart API receipt.
  Real evidence, Watch and Finding lists remained empty through the actual API.
- A full regression run caught an enclosing-transaction incompatibility in the
  initial evidence snapshot change; it was repaired before the final full pass.
  Independent Spec review caught premature completion for zero-row extraction
  before its filing-evidence link committed; that was repaired and regression
  tested. Final independent Standards/security and Spec reviews have no remaining
  findings. The optional duplicated normalization predicate was consolidated.
- Credential/private-key checks found no matches in the ten-file inventory or
  generated frontend JavaScript. All 89 pre-existing excluded research files,
  the schema, and the legacy database are byte-identical to the pre-work snapshot.
  The legacy SHA-256 remains
  `ab5ccffa55e46e7d195204419602357e233d7c6da8aa2f5ba4390305f6739da3`.

Verdict: **CONDITIONAL PASS**. The approved offline/test Stage 2 acceptance
criteria pass. House acquisition/retention rights and live readiness remain
unresolved; production market-data readiness remains unavailable. There is no
annual-index replay, complete transaction/historical coverage, or new permission
claim. Loopback protection remains a local single-user boundary, not protection
against another process/user already on the machine. Restart recovery requires
explicit Resume; pre-validation errors are not a persistent attempt ledger.

## Exact suggested commit inventory

```text
docs/f2-stage-2.md
frontend-tests/capabilities.test.ts
server/disclosures.py
server/offline_house.py
server/routers/disclosures.py
server/tests/test_offline_house.py
src/data/houseFiling.ts
src/data/useDisclosureEvidence.ts
src/detail/HouseFilingEvidence.tsx
src/detail/HouseFilingIntake.tsx
```

New files are the Stage 2 note, offline corpus module and corpus tests. All
remaining listed files are modified. Suggested message:
`feat(f2): add bounded offline House corpus and processing recovery`.

Exclude the pre-existing publication-manifest change, OpenFIGI transfer JSON,
Stooq and Twelve Data experiment directories, runtime databases, screenshots,
downloaded local copies and build outputs. No fixtures, schema, approved
specifications, readiness decisions, collectors, scheduler or README changed.
No staging, commit, branch/reference mutation or GitHub-state update was made.
Work stops after Stage 2 for project-owner review.
