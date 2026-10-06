# Market-data conformance boundary (#31)

Authority: approved [#26](https://github.com/AviSharma01/signal-workspace/issues/26),
[#10](https://github.com/AviSharma01/signal-workspace/issues/10), and implementation
contract [#31](https://github.com/AviSharma01/signal-workspace/issues/31).
This describes the implementation, not a provider adoption decision.

`MarketConformanceApplication` is the offline application seam. A
`CandidateMarketAdapter.conformance_evidence(scope)` returns retained snapshots,
case observations, explicit unsupported cases, references from each observation
to snapshots, and workload provenance. The harness does not fetch data, choose a
provider, run refresh jobs, or execute Event outcomes.

The evaluation scope declares its identity, evidence class (`synthetic` or
`real_candidate`), evaluation instant, coverage, securities, calendar version,
and independently attributed expected observations. Expectations must be
established outside the adapter and its transformations. Their independence and
external authority require human review; equality alone cannot certify their
truth. A candidate's self-declared pass flag is not an input.
The adapter must also implement `replay(scope, evidence)`: it receives retained
source snapshots with normalized semantics and observed answers removed, and a
scope with expected answers removed. It must rebuild semantics and observations
from retained inputs without external access. Missing replay is unsupported;
failed or differing replay fails reproducibility. `reproduce(report, adapter=...)`
repeats this check. Adapter replay implementations themselves require independent
review before a real candidate can be approved.

Every required gate/case in `GATE_CASES` must have nonempty independent expected
and observed records and valid retained snapshot references. A missing expectation,
observation, reference, or explicitly unsupported case is `unsupported`.
Disagreement or an invalid supplied semantic/operational contract is `fail`.
All cases must pass, including required case fields, retained-input replay,
identity validity intervals, action identity/terms/date checks, a representative
raw close/open calculation check, and structural snapshot checks, for the exact scope's
conformance capability to be `available`. Some passing gates with unmet gates
are `conditional`; no passing gates is `unavailable`. Case details preserve
failed versus unsupported evidence even when both occur in one gate.
Matching expectations cannot relax mandatory outcomes: reused ticker histories
must be separated with distinct retained historical identity mappings; later
revisions must preserve earlier evidence; and bounded refresh evidence must name
a non-empty, explicit session scope. Missing identity support is unsupported;
contradictory outcomes or malformed supplied scope fail. No refresh scope is inferred.

The contract includes history (five complete calendar years plus the current
year through evaluation), retention rights and zero-cost feasibility, raw daily
regular-session OHLCV/feed definitions, calendars, identity/listing joins,
actions, terminal events, currency/units, missingness, acquisition/backfill/
catch-up, revisions/repeated retrieval, disagreements, temporal boundaries,
independent calculations, provenance, reproducibility and operational workloads.
Calendar, identity and calculation cases compare independently established
expectations with candidate observations; this is an acceptance harness, not a
new calendar dataset, identity resolver, or return engine.

Snapshots retain source bytes as base64 in exported reports, separately from
normalization and semantics. They retain evidence class, source, request parameters, retrieval
observation and instant, revision identity, normalization version, historically
scoped security/listing mapping evidence, observed symbol, exchange/session,
calendar version, timezone, currency/units, OHLCV definitions/feed coverage,
raw/provider/application adjustment distinction, separately attributed actions
and their date meanings/terms/units/availability, missingness/gaps and finality.
Under #26 §6, unresolved terminal-action windows have no numeric terminal
return; the delisting case requires `None` until a later deterministic treatment
is approved. Source-provided action terms remain retained separately.
An empty action list means explicit no-action evidence; action conformance cases
still require separately attributed records of the action being tested.

The JSON report retains the entire scope and submitted evidence, every gate/case
decision, versions and a deterministic evidence digest. `reproduce(report, adapter=...)`
checks the digest and supported versions and reevaluates the retained inputs;
modified inputs or decisions fail reproduction. Callers can retain this JSON as
an evaluation artifact without database writes. No production persistence,
provider approval command, or environment switch exists in this slice.

Operational cases retain backfill, acquisition/catch-up, revision, joins and
representative calculation observations, bounded revision-refresh validation
(policy version, session scope and preservation evidence), request counts, elapsed milliseconds,
peak memory bytes, retained storage bytes, method/environment and input
references. Measurements must be nonnegative and finite. No performance target
or revision-refresh policy is approved here. Synthetic measurements demonstrate
the evidence shape only; they establish no real-provider operational claim.

## Isolation and capability API

`production_market_readiness()` is independent of every conformance report,
adapter, fixture, legacy price row, seed and environment variable. It returns
`unavailable`, all exact gates as unsupported, and `explicit_provider_approval`.
`/api/capabilities` exposes it as `market.data_readiness`; existing dependent
capabilities include its unmet gates while retaining #30's reason codes and
separation of availability from result state. No fixture upload/evaluation API
is registered. Production modules never import the fixtures.

Fixtures live exclusively under `server/tests/`. Candidate source observations are
retained in `fixtures/market_conformance/candidate.json`; worked expectations
are declared separately in `market_fixture.py`. Its test-only adapter decodes
retained source JSON and independently recomputes the toy close/open observation. They are toy records, not a
real exchange calendar or historical provider coverage. Even a complete
`real_candidate` report is only an evaluation decision and cannot activate
production. Future adoption must independently validate all real evidence and
receive explicit human approval through separately approved application work.

## #31 → #32 handoff

#32 can consume retained raw snapshots with explicit identity/calendar/action/
currency/provenance semantics and scope-specific conformance decisions. It must
check production readiness at execution and must not infer readiness from
snapshot presence or a successful synthetic report. There is no approved
production provider, so its production outcome path remains unavailable.
The representative toy close/open calculation is only a conformance observation;
no Event outcome, benchmark-relative calculation or cohort engine was added.
