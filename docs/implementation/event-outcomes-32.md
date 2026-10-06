# Per-Event outcomes (#32)

Authority: approved [#26](https://github.com/AviSharma01/signal-workspace/issues/26)
§§4–6, 8–9, 14–15 and [#32](https://github.com/AviSharma01/signal-workspace/issues/32).
This is an implementation description, not provider approval or new methodology.

## Inputs and execution boundary

`AnalysisApplication` consumes a recorded #28 public-information historical
Event view and an explicitly retained #31 conformance report. It never derives
an Event from a price, modifies Event/Watch state, or uses outcome evidence to
resolve an earlier disclosure identity, field, eligibility or anchor. The
recorded view supplies occurrence identity, original anchor/calendar citation,
intrinsic boundary, frozen fields/identities, As-Of perspective, disclosure
eligibility, raw/derived evidence provenance and input versions. Corrected-
retrospective and system-observation views cannot execute the primary method.

`retain_evaluation(report, population=..., adapter=...)` verifies #31 retained-
input replay and complete conformance before appending its exact report. Raw
source bytes, normalized semantics, retrievals, revisions, evidence class and
independent expectations remain retained. There is no provider fetch/integration,
production approval command, fixture upload HTTP API, or environment bypass.

Production execution checks `production_market_readiness()` before reading any
inputs. Snapshot presence and conformance availability cannot authorize it.
Production remains unavailable under #31. Real storage refuses synthetic inputs;
SQL constrains production runs to production scope. Test/evaluation execution
requires a complete named **synthetic** conformance scope, matching synthetic
snapshots and isolated population. Its outputs explicitly have
`production_ready=false`. Production queries cannot read those inputs/runs.

The readiness scope must contain the measured security/session dates and exact
calendar version. Each required bar also undergoes #31 semantic validation.
Supplemental normalized snapshot semantics supply `open_at`/`close_at`,
`identity_evidence.public_at_ms` and `listing_country`, and a retained `calendar`
with source/revision, calendar ID/timezone, public availability, certified coverage
and the ordered complete regular sessions. Calendar evidence may be retained in
another bar snapshot; it need not be repeated on every anchor bar. Unsupported,
future or ambiguous calendar/identity evidence withholds dependent measurements.
SPY is identified as the historically mapped SPDR S&P 500 ETF Trust, with retained
listing/identity evidence; a ticker-only match is insufficient. No approximation,
mixed-source fallback, unvalidated venue change, or listing stitching is allowed.

## Method `event-outcomes@1`

The Event Anchor is session 1. Windows contain exactly 1/5/20/60 regular sessions;
20 is marked primary. Start is the anchor open, Outcome Boundary the final close.
The retained calendar, rather than observed bar count, determines required dates.
A missing observation cannot shorten a window. A calendar lacking a terminal
session yields an unknown boundary and unavailable result, never a shortened return.

For each instrument the gross factor starts with raw anchor close/open. Each
later included session multiplies `(split-normalized close + split-normalized
ex-date cash) / prior split-normalized close`. Splits multiply the share basis by
the retained new:old share ratio; they create no economic return. Cash reinvests
at ex-date close. Anchor-date cash is excluded. Split and cash evidence can be
retained before their effective/ex dates. Repeated identical action evidence is
used once; conflicting revisions/terms remain ambiguous. Explicit `action_id`
can distinguish separate distributions on the same date; no inferred action
reconciliation is performed.

Security and SPY gross factors use the same exact dates/timestamps. Relative log
return is `ln(security gross / SPY gross)`; compounded relative return is
`exp(relative log) - 1`. Purchase multiplies the log outcome by +1, sale by -1.
Direction does not negate the reported compounded relative return. Raw total
returns are gross factors minus one. Arithmetic uses an explicitly fixed Decimal
context (34 digits, round-half-even), with JSON numeric outputs and no percentage
rounding in calculation. Application adjustments cite retained action snapshots;
source raw and provider-adjusted fields are never rewritten.

Each metric has its own value, availability and stable, non-exclusive reasons.
Unavailable values are null. Missing bars/fields, incompatible sessions,
unresolved identities/currency/units, adjusted-only data, unvalidated source/feed
changes and ambiguous bars/actions withhold only dependent measurements. There
is no fill, interpolation, substitution, zero replacement or terminal-price
invention. Non-cash/merger/spin-off/delisting/listing/terminal uncertainty is
unavailable in affected windows. Security failure preserves independently valid
SPY metrics; benchmark failure preserves independently valid security metrics.
Pre-close retrieval cannot support a completed-session return.

## Retention, APIs and read view

`analysis_market_inputs` retains the exact report, content-addressed by #31's
input digest. `analysis_runs` appends a fresh run for every execution, atomically
storing all outcomes and the manifest. No update/delete path exists. A revision
creates a different retained input identity and separately attributable run.
Each run retains the Event view and input manifest, method/market-contract
versions, population/readiness decision/scope, calculation instant, per-window
boundary/dates, separate security/SPY snapshot identities/revisions/retrievals,
applied action provenance, metric reasons and disclosure/window coverage counts.
These are descriptive counts, not cohort estimates or inference.

Reproduction uses the exact recorded Event view, market input identity, retained
method implementation and supported retained contract version. It verifies input
digests and outcome equality. It does not use latest data/default method, append
another result, or reinterpret current production readiness as historical authority.
Unknown retained methods/contracts are rejected rather than silently upgraded.

- `GET /api/analysis`: production readiness and retained production runs.
- `POST /api/analysis/runs`: explicit execution using `eventViewId`, `marketInputId`.
  Returns 409 with unavailable capability/error result while production is blocked.
- `GET /api/analysis/runs/{id}`: exact production run and current capability.
- `GET /api/analysis/runs/{id}/reproduction`: verified retained-version reproduction.

HTTP routes force real population and reject population/readiness overrides.
`/analysis` is a minimal read view linked from disclosure evidence: existing
capability notices, per-Event table, metric missingness and expandable provenance.
It additionally withholds any non-production run. Unavailable production has an
error result and blocking prerequisites, never an empty successful Analysis.

## Acceptance and #33 handoff

The focused tests exercise independent endpoint/log/compounded goldens for all
four horizons, purchase/sale, SPY, holiday/early-close/exact-at-open anchors,
splits, cash reinvestment/anchor exclusion, action revisions, intermediate/
terminal missing bars, calendar/session incompatibility, identity/currency/unit
uncertainty, terminal actions, source disagreement, snapshots/repeated execution,
old-version reproduction, future evidence, production refusal, scope validation
and test/evaluation-to-production isolation. Frontend render tests cover explicit
blocked/error states, per-metric nulls, provenance, primary horizon and synthetic
withholding. Expected values never call production arithmetic.

#33 receives immutable per-Event outcomes, primary/supporting horizon labels,
frozen Event metadata/provenance, metric availability/reasons, disclosure/window
coverage, retained snapshot IDs and run/method/readiness identity. It must perform
cohort selection, aggregation, member/episode sensitivities, uncertainty and
statistical reporting under its own approved contract. None is implemented here.

Production cannot execute until separately approved real-provider evidence and
explicit production readiness exist. Fixtures demonstrate calculations and
isolation, not real coverage, a production calendar or operational readiness.
No provider, fallback or revision-refresh policy is selected by this work.

## Verification (2026-10-06)

- Focused application/API goldens and boundary tests: **28 passed**.
- Full backend suite: **198 passed**.
- Frontend render/contract tests: **7 passed**.
- Python compilation, TypeScript project checks, ESLint and production build: passed.
- Secret scans (source/fixtures and fresh bundle), production fixture-import/
  bundle scans, and tracked/new-file whitespace checks: passed.
- Standards and Spec reviews: all reported findings resolved; no remaining
  actionable findings. Review included session indexing, anchor timing, raw versus
  adjusted prices, action evidence, missingness, revisions, readiness isolation,
  forbidden future evidence and exact approved formulas.
- Frontend checks used bundled Node 24.19 because default Node 20.16 is below
  current Vite requirements. No project runtime/configuration change was made.
  Existing large-chunk and test-client deprecation warnings remain non-blocking.

Acceptance checklist:

- [x] Explicit production readiness required; production remains unavailable.
- [x] Anchor included, exact sessions retained, missing windows never shortened.
- [x] Security/SPY gross factors use approved raw open/close, split and cash rules.
- [x] Relative log, exponential compounded and direction-aligned outputs deterministic.
- [x] Incompatibility/missingness/actions/identity/units affect dependent metrics/windows.
- [x] No zero replacement, imputation, fills or substituted observations.
- [x] Repeated execution appends runs; revised inputs and older reproduction stay attributable.
- [x] Synthetic readiness/results are isolated and cannot publish production-ready outputs.
