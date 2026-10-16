# F2 Stage 1: safe local, offline House filing inspection

Scope: the project owner's Stage 1 approval on 2026-10-16. Stages 2–5 are
not implemented here. This is a bounded offline workflow, not operational
House source readiness or production market-data readiness.

## Source access decision

Reviewed on 2026-10-16:

- [House access notice](https://disclosures-clerk.house.gov/FinancialDisclosure/ViewSearch)
  prohibits unlawful use, specified commercial use, credit-rating use and
  solicitation. It does not expressly address this automated collection and
  retained-copy workflow.
- [House Ethics Manual: public access](https://ethics.house.gov/manual/retention-of-and-public-access-to-reports/)
  describes public availability and restrictions, including requirements for
  requesting reports on file. It does not establish an automated-retention
  authorization for Signal.
- The Clerk's robots file could not be inspected with the research tool.
  That failure proves neither permission nor prohibition.

Personal, noncommercial research is not one of the listed prohibited purposes,
but compatibility of the complete automated acquisition/retention route remains
unresolved. Successful HTTP access is not permission. No new filing or annual
index was downloaded from the House. The approved fallback is used instead: inspect the already
retained official `2021-20018021.pdf`, described by the existing
[fixture manifest](../server/tests/fixtures/house_ptr/README.md).

Live House index/filing API retrieval returns HTTP 409 with
`house_live_access_unresolved`. No runtime switch bypasses that restriction.
Resolving it requires a later explicit source-access decision, not a successful
test or an available endpoint. This does not claim personal research is unlawful.

## Start an isolated local instance

From the repository root, create the ignored local output directory:

```sh
mkdir -p server/.local
```

In a backend terminal:

```sh
cd server
export SIGNAL_F2_DB="$PWD/.local/f2-stage1.sqlite3"
./venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

In a frontend terminal, from the repository root:

```sh
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open `http://127.0.0.1:5173/disclosures`. Use **Inspect retained sample**, expand
the row and local observations, and download the exact retained PDF if desired.
Reading it again adds a local observation without another version or row.
Reloading or restarting preserves the selected database's evidence.

An explicit absolute `SIGNAL_F2_DB` selection is required before database access;
there is no default database. Runtime files must be inside the canonical
`server/.local/` directory and their parent directory must already exist. Traversal
(`..`), symlinked roots/paths, nonregular files and files with more than one hard
link are rejected. The same link checks protect SQLite journal/WAL/SHM sidecars.
`server/signal.db` and its aliases are always rejected, including through test
injection. No migration or copy of the legacy database is automatic.

Initialization distinguishes a nonexistent file from an existing database:

- A new file is created exclusively, with owner-only permissions, and receives
  the V2 schema and SQLite application ID `0x53494732` (`SIG2`). No companies or
  other unsupported real-population records are seeded.
- Existing files are inspected read-only before any read/write connection or
  migration. They must have the exact known Stage 1 schema and either the Signal
  application ID or ID zero for the previously unmarked Stage 1 implementation.
  A recognized unmarked F2 database receives the ownership ID at initialization.
- Unknown owners, arbitrary SQLite files (even inside `.local/`), pre-existing
  empty files, partial initialization and schema drift fail closed without
  migration. An application ID alone cannot authorize an unrelated schema.
  Future schema changes must explicitly support their predecessor; this is not
  a general-purpose database adoption or migration system.

Existing user rows, including bootstrap company rows already present in an old
F2 database, are preserved. Preservation does not validate their identity or
provenance. Initialization adds no real entities; new real entities require
their appropriate evidence-backed application path. The existing explicit
`seed_demo.py --demo` path remains isolated in the demo population. V2 population
constraints are unchanged.

Trusted tests may inject an isolated temporary `DB_PATH` programmatically. This
is not a runtime environment option; it permits compatibility tests on temporary
legacy copies without opening a production import path. Legacy-file and link
protection still apply to this injection.

Startup registers only the existing Watch recovery interval and startup recovery.
Existing known-expiry scheduling remains intact. Yahoo prices/news, Stocktwits,
House catch-up and daily discovery are not registered. The old collection
functions remain in the repository but are not F2 entry points. This bounded mode
does not satisfy full V2 daily discovery or chamber-readiness requirements.

The service accepts loopback peers and loopback Host names only. Browser mutations
require JSON and an allowed local Origin when present. Originless requests with
cross-site Fetch Metadata are rejected; embedded browsers may label an explicitly
allowed loopback Origin cross-site. Local CLI JSON requests may omit Origin.
Supported browser origins are HTTP localhost/127.0.0.1/[::1] on ports 5173 and 8000. Use the documented
launch command, without a reverse proxy. This boundary is not authentication
against another process/user already on the machine; no login is introduced.

## Evidence and population boundaries

- The sample is an official-source artifact in the **test** population. It is
  never promoted to real merely because its original source was official.
- Only dedicated `/api/disclosures/offline-sample` routes expose this declared
  sample. Real evidence, Event, Watch and Finding queries remain separate.
- An observation records an actual local sample read, `httpStatus: null`,
  `observationKind: offline_sample_read`, unknown original retrieval instant,
  unknown live source availability, freshness and coverage. It is not a newly
  observed HTTP retrieval or historical publication claim.
- The fixed fixture's independently recorded SHA-256 is checked before ingestion
  and raw download. No caller-supplied source URL, file path, payload, population
  or timestamp is accepted by this sample command.
- Existing V2 extraction/normalization and retained-content storage are reused.
  The source PDF is not modified or copied into another tracked artifact.
- The sample has one extracted transaction row and one suitable security/date
  reference. No identity, publication time, security continuity, Watch admission
  or Finding is fabricated. Stage 3 still requires a measured real-reference
  workload; if a later bounded corpus has fewer than twenty suitable distinct
  references, report that shortfall instead of manufacturing diversity or
  selecting only easy cases.

## Backup, migration and recovery

Keep runtime databases under `server/.local/`; backups may also be stored outside the checkout. Do not commit them.
Before testing a migration on a valued selected database,
stop the backend and make a SQLite backup to a new filename. For example, with
the SQLite CLI installed, from the repository root:

```sh
sqlite3 server/.local/f2-stage1.sqlite3 ".backup 'server/.local/f2-stage1-before.sqlite3'"
```

Stop other writers before initialization/migration: ownership inspection is an
immutable read-only snapshot and does not recover journals or incorporate
pending WAL changes. Test startup against a **temporary copy** of a consistent
SQLite backup. Runtime rehearsal copies must also be inside `server/.local/`;
temporary test-only injection is a separate trusted test path. Run `PRAGMA quick_check`
and `PRAGMA foreign_key_check` on the copy, compare source-row counts/values and
population separation, and initialize it twice. Existing additive V1 migrations
are preserved; legacy disclosure/Findings tables do not become V2 evidence.

If recovery is necessary, stop the backend, preserve the failed database for
inspection, copy a recognized F2 backup to a new filename inside `server/.local/`,
and explicitly select that canonical copy with `SIGNAL_F2_DB`. Never overwrite
`server/signal.db` or the backup. Do not stamp an arbitrary database with the
Signal application ID to bypass rejection. Unknown or modified schemas require
separate review; no downgrade, destructive reset or automatic legacy import is
provided.

## Verification and limits

Backend tests exercise the actual FastAPI app's local boundary and offline
routes, missing/tampered samples, duplicate reads, exact-byte downloads,
population isolation, unchanged production capability gates, explicit database
selection, legacy aliases, migration compatibility and Watch recovery.
Frontend tests check provenance/unknown-time labels, source-text escaping,
retained-version links and pending/error states. Browser verification must use
the real running app, not a mocked fetch or fixture promoted to real.

No identity ledger, broad backfill, scheduler redesign, login, paid service,
market-data integration or q integration is included. #31 and approved V2
methodology are unchanged. Live acquisition and source readiness remain
unavailable; Stage 1 acceptance uses the explicitly isolated offline fallback.

## Initial Stage 1 browser receipt (before database remediation)

Verified in the running browser against the explicitly selected
`server/.local/f2-stage1.sqlite3`: one official-source test artifact, one retained
version, one extracted row, and two local sample-read observations. Reloading
and restarting the backend retained the evidence. The exact PDF downloaded through the application matched
the fixture's 56,079 bytes and manifest hash
`071aab65d8223132ac372501605fadc98948e3c8f0faa006931ea3902c86d7c2`.
Real evidence, Watches and Findings remained empty. Browser verification initially
caught an embedded-browser Fetch Metadata mismatch; a regression test now checks
explicitly allowed local Origins without admitting unknown Origins.

The existing `server/signal.db` remained byte-identical to its pre-work hash
`ab5ccffa55e46e7d195204419602357e233d7c6da8aa2f5ba4390305f6739da3`.
Migration verification uses both a constructed legacy database and a temporary
SQLite backup of the actual local legacy database, with repeat initialization,
integrity/FK checks and digests of original source values.

Verification commands, backend commands run from `server/`:

```sh
PYTHONPATH=.:tests ./venv/bin/python -B -m unittest discover -s tests -t .
./venv/bin/python -B -m unittest tests.test_f2_startup
```

Frontend/repository commands, run from the repository root:

```sh
npm run test:frontend
npm run lint
npx tsc -b --pretty false
npm run build
git diff --check
```

The test directory must be on `PYTHONPATH` because existing conformance tests
import `market_fixture` as a top-level module. The build retains its existing
large-chunk warning; no bundle restructuring is part of Stage 1.

The initial implementation passed 273 backend and 12 frontend tests, but the
independent audit subsequently identified its overly broad DB selection and
unsupported real-company seeding. Those initial results did not establish the
corrected database boundary. Current remediation verification is recorded below.

## Focused Stage 1 security remediation

Scope is only the two database blockers, their compatibility tests, and the
missing Watch lifespan/restart regression. The runtime boundary and seed removal
above replace the initial Stage 1 database policy.

The new regression launches two separate backend processes against the same
temporary database containing two synthetic, previously admitted Watches. It
uses the actual FastAPI lifespan and actual APScheduler startup callback, without
calling recovery directly or replacing the scheduler. It verifies overdue expiry
is recorded at the actual recovery time, a future expiry job is rebuilt, and
cold restart preserves admission/history without duplicating transitions. All
registered jobs must belong to Watch recovery/expiry; external connections are
forbidden during the test. Synthetic records never enter a user database.

Database tests cover unrelated files inside/outside the canonical directory,
traversal and directory/file symlinks, hard-linked recognized F2 files, unsafe
sidecars, unrecognized/spoofed owners, empty files, fresh empty populations,
recognized pre-marker migration and repeated reopen. Legacy-copy tests retain
original source values and the actual legacy file's hash. Existing offline
provenance/idempotency and local mutation protections remain under regression.

The pre-existing legacy prices endpoint's reported HTTP 500 is a separate
follow-up: its router/implementation is unchanged by this remediation.
Live House acquisition/retention remains unresolved, market functionality remains
gated, #31 is unchanged, and no Stage 2 work is included.

Focused verification command (from `server/`):

```sh
./venv/bin/python -B -m unittest tests.test_f2_startup tests.test_f2_watch_startup tests.test_legacy_population tests.test_watch_jobs tests.test_disclosure_jobs
```

Results: **279 full backend tests, 23 focused regression tests and 12 frontend
tests passed**. Lint, TypeScript, build, credential/security checks and
`git diff --check` passed. The build has a nonblocking large-chunk warning.
All five remediation paths were inspected for scope, secrets, unexpected data
and unintended behavior. The aggregate content hash of all 89 unrelated research
paths, including the modified publication manifest and provider bundles, is
unchanged; the legacy database hash above is also unchanged. These paths are
excluded from the commit inventory, as are generated/runtime artifacts.

Both database blockers and the missing regression are resolved. Verdict:
**CONDITIONAL PASS** for Stage 1 solely because live House source rights/readiness
remain unresolved; the approved offline path and focused security remediation
pass. Existing bootstrap rows are preserved rather than deleted or retroactively
certified. No Git staging, commit or other Git-state mutation was performed.

Only these paths changed during remediation:

```text
server/db/database.py
server/tests/test_f2_startup.py
server/tests/test_f2_watch_startup.py
server/tests/test_legacy_population.py
docs/f2-stage-1.md
```

## Exact suggested commit set

```text
.gitignore
docs/f2-stage-1.md
frontend-tests/capabilities.test.ts
server/db/database.py
server/jobs/scheduler.py
server/local_access.py
server/main.py
server/routers/disclosures.py
server/tests/test_disclosure_jobs.py
server/tests/test_f2_startup.py
server/tests/test_f2_watch_startup.py
server/tests/test_legacy_population.py
src/data/api.ts
src/data/houseFiling.ts
src/data/useDisclosureEvidence.ts
src/detail/DisclosureEvidencePage.tsx
src/detail/HouseFilingEvidence.tsx
src/detail/HouseFilingIntake.tsx
tsconfig.frontend-tests.json
```

Suggested message: `feat(f2): add safe local offline House filing inspection`.
Runtime databases, screenshots, downloaded PDFs, build outputs and pre-existing
research changes are excluded. No new source PDFs, credentials or provider
payloads belong in this commit. No staging or commit was performed.
