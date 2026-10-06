# Bounded investigations and validated Findings (#34)

Descriptive implementation notes for this uncommitted #34 working-tree change,
starting from the existing #29/#30 application boundaries. Authority remains
[#26](https://github.com/AviSharma01/signal-workspace/issues/26),
[#34](https://github.com/AviSharma01/signal-workspace/issues/34), and repository
AGENTS instructions. These notes introduce no new methodology or readiness approval.

## Traced boundaries and reuse

V1 `agent/loop.py` requires a backend, dispatches global ticker tools, and uses a
latest-market-bar anchor; `agent/finding.py` does not validate evidence citations
or free-text advice. Its tools, categories, prompt, spend guard, scanner, and
Finding persistence are excluded from V2 execution. The normalized-backend concept
is suitable for future bounded optional adapters, but no provider is configured
by #34. Existing V1 records remain excluded from V2 APIs.

The implementation reuses #27 retained disclosure evidence and provenance,
#28 Event identity and public/system temporal rules, #29 Watch lifecycle and
immediate authorization, #30 capability/result contracts, `get_connection()`,
and the existing disclosure/Watch and company Findings navigation surfaces.
`event-pit@1` recorded envelopes remain unchanged. The shared temporal helper
preserves existing derivation behavior; the separate investigation snapshot
adds no fields to recorded Event views.

## Commands, retention and execution

`POST /api/investigations` requires an explicit Event/Watch trigger, an explicit
Public-information/System-observation As-Of instant, step and elapsed-ms budgets,
and optionally a model-spend ceiling. The strict command rejects caller-supplied
evidence, capabilities, trigger versions and extra quota dimensions.

Creation freezes the trigger identity/version, boundary, eligible evidence and
its publication-proof dependency closure, source hashes/locators/observation
references, capability catalog, versions, budgets, mode and manifest digest in
one transaction. Read-only tools receive only frozen in-memory copies, with
`list_evidence` and `read_evidence`; they have no DB, network, ingestion, source
repair or persistence handles. Tool arguments cannot alter the boundary.

Watch triggers use #29's admitted original occurrence even after a verified
Event merge. A Watch trigger requires system-observation semantics and admission
known at its boundary. Historical non-active investigations do not require active
status. Active-only requests use #29 authorization at creation and again at
execution, inside the application transaction; a prior UI/API response is not
execution authorization. Later lifecycle evidence affects authorization only,
never the frozen tool-visible evidence set.

`POST /api/investigations/{id}/execute` is idempotent. Deterministic execution
inspects eligible retained disclosure evidence and may conclude unexplained,
insufficient eligible evidence, capability unavailable or budget exhausted.
It makes no causal, market or statistical explanation. Steps include the
orchestration decision and tool calls. Deadline checks cover freeze duration,
queued elapsed time, execution, tools and successful Finding validation. An
overrun discards completion and validates a terminal budget-exhausted outcome.
Budget checks do not interrupt SQLite snapshot reads; failed/overlong reads
cannot become a completed Finding. Terminal validation/persistence is necessary
application bookkeeping after an exhausted budget, not continued investigation.

Optional-model mode has an explicit unavailable capability and no live adapter.
A zero spend ceiling stops the request before any model call. The budget seam
supports reserving a declared maximum cost before a future bounded optional
adapter call; no API spend occurs in this implementation. No global/monthly or
evidence-item quotas are added.

Run completion and its validated Finding are stored together in the same
application-owned SQLite row/transaction. The manifest cannot be updated. Tools
and model code have no persistence path. Reproduction replays the deterministic
inspection/decision path using frozen evidence, capabilities, recorded #29
authorization and actual recorded elapsed/step/spend checkpoints, compares the
entire execution, and reconstructs/compares the validated Finding. It never
rechecks current evidence or simulates a faster historical deadline.

## Validation and display

The application validates allowed structure, trigger/run identity, exact boundary,
allowed outcome, claims/counterevidence citations, membership in the inspected
eligible set, source provenance/hash/locator and timing, unresolved questions,
confidence and basis, missingness/limitations, frozen capability limitations,
method/model versions, review status, no-advice status and null structured advice.
Unknown structured fields are forbidden. Confidence cannot substitute for a claim
citation.

Free text is checked for explicit advice, including Unicode-normalized forms.
Acceptance additionally requires the controlled deterministic prose contract;
arbitrary narrative is withheld even when a keyword filter misses a paraphrase.
`validate_proposal` returns an explicit review-required rejection with reason
codes and a digest, without saving/displaying raw rejected prose or altering the
retained Finding. No human approval bypass or narrative-promotion UI is shipped.
Raw source text remains unchanged as evidence; it is never interpolated into a
validated Finding. Every retained Finding is revalidated before API display.

`GET /api/investigations`, `GET /api/investigations/{id}` and
`GET /api/investigations/{id}/reproduction` expose runs/provenance/status.
`GET /api/findings` exposes validated V2 Findings only. The existing disclosure
page starts explicit bounded runs and displays budgets, manifest/trigger versions,
frozen capability states, outcomes, citations and limitations. The company panel
links to Event/Watch investigations and filters only retained normalized literal
ticker fields: asset names and resolved security IDs are never guessed into a
company/ticker join. Official records lacking such a ticker field remain available
on the Event/Watch surface.

Capability availability is supplied by #30, separate from ready/complete/incomplete
run status and empty/partial/successful request state. Market-triggered
investigation and selection evaluation remain unavailable. No independent target
or declared baseline exists; counts, narrative length and confidence do not
activate evaluation or become success metrics. No graph, anomaly, market-data,
Analysis, Consensus or q behavior is introduced.

## Acceptance and verification seams

All eight #34 acceptance criteria are implemented:

- Frozen boundary/eligible evidence and strict tool arguments prevent widening or
  future/ineligible evidence access under each temporal perspective.
- Evidence tools operate on copies without mutation/retrieval/side effects.
- Model absence, inadequate evidence and budget exhaustion have explicit outcomes.
- Claims/counterevidence require inspected eligible citations with exact provenance
  and timing; an unexplained result may honestly have no counterevidence established.
- Invalid citations, unsupported categories and advice-bearing output are withheld
  through application validation and the explicit proposal rejection path.
- Creation/completion/Finding persistence is application-owned and atomic.
- Core execution and deterministic reproduction work without an LLM.
- Market-triggered investigation remains unavailable with no new anomaly criteria.

Tests run at the approved application/API and read-only tool/budget seams.
Focused coverage includes both temporal perspectives, later corrections and
unknown public availability, publication-proof closure, extraction timing,
copy isolation, denied retrieval and mutation, step/time/spend stops, unavailable
models, valid unexplained/insufficient outcomes, citation/structure/text rejection,
atomic crash/retry, manifest immutability, population isolation, capability
snapshots, immediate Watch authorization/expiry/merge, and decision reproduction.
Frontend tests verify separate capability/result states and visible audit fields.
Final check results are reported in the chat after full verification.

## Concrete completion boundary

#34 provides explicit manual Event/Watch investigations over retained disclosure
and assertion evidence with conservative deterministic Findings. No automatic
selection/trigger, market explanation, external retrieval, live model adapter,
arbitrary-narrative approval, or independently judged evaluation is activated.
Source/market readiness limitations remain those of the upstream contracts.

## Files changed in this task

- `docs/implementation/investigations-34.md`
- `frontend-tests/capabilities.test.ts`
- `server/capabilities.py`
- `server/db/schema.sql`
- `server/events.py`
- `server/investigation_contract.py`
- `server/investigation_runtime.py`
- `server/investigations.py`
- `server/main.py`
- `server/routers/findings.py`
- `server/routers/investigations.py`
- `server/tests/test_capabilities_api.py`
- `server/tests/test_investigations.py`
- `server/tests/test_investigations_api.py`
- `server/tests/test_v1_capability_containment.py`
- `server/watch_events.py`
- `src/data/api.ts`
- `src/data/investigationTypes.ts`
- `src/data/useFindings.ts`
- `src/data/useInvestigations.ts`
- `src/detail/DisclosureEvidencePage.tsx`
- `src/detail/FindingCard.tsx`
- `src/detail/FindingsPanel.tsx`
- `src/detail/InvestigationResults.tsx`
- `src/detail/InvestigationsPanel.tsx`
- `src/detail/WatchEventsPanel.tsx`

## Scoped review

The implement skill’s Standards and Spec reviews used the task-start filesystem
snapshot rather than a Git history comparison. Standards found no actionable
violations. Spec identified final-validation deadline accounting and decision
reproduction gaps; both were fixed and regression-tested. Subsequent Spec review
confirmed those fixes and the publication-proof/Watch-merge audit fixes with no
remaining actionable findings. No issue, PR, staging, branch or commit mutation
was performed. The sole Git command was the explicitly requested read-only
`git diff --check`; new files also passed a direct whitespace scan.

## Final check results

- Focused #34 application/tool/budget/API suite: 30 passed.
- #29 Watch/lifecycle/API/job regression suite: 46 passed.
- #30 capability API and V1 containment regression suites: 6 + 3 passed.
- Full backend suite: 254 passed on the final run (123 seconds).
- Frontend rendering suite: 10 passed.
- TypeScript (`tsc -b`), ESLint, production build, Python compilation and
  changed-file Prettier checks: passed.
- Source/config/fixture and built-bundle secret scans: 2 passed.
- Population/fixture isolation and read-only/no-network regressions: passed.
- `git diff --check` and direct changed/new-file trailing-whitespace scan: passed.
- Standards review: no actionable findings. Spec review: both initial findings
  fixed and verified; final focused re-reviews found no remaining actionable gaps.

The first full backend run had one pre-existing timing-dependent failure in
`test_disclosure_jobs`: `FakeHouseSource.fetch_index` uses ZIP creation timestamps,
so identical XML can have different retained byte hashes across a two-second DOS
clock boundary. Both task-start and changed checkouts passed the test in isolation;
advancing only the mock ZIP clock reproduced the same failure in the task-start
snapshot. Its fixture and production ingestion were left unchanged. The complete
suite then passed without patches. Existing warnings remain for the Starlette
httpx test-client deprecation and the frontend chunk-size threshold.
