# Deterministic cohort Analysis (#33)

Authority: approved [#26](https://github.com/AviSharma01/signal-workspace/issues/26)
§§5, 7–9, 14–15 and [#33](https://github.com/AviSharma01/signal-workspace/issues/33).
Empty episode draws additionally follow the explicit approved
[2026-10-06 supplement](../specs/cohort-empty-bootstrap-33.md). This describes
implementation of those approvals and does not adopt providers.

## Retained #32 boundary

`CohortAnalysisApplication` reads one immutable `AnalysisApplication.get_run`
output. That output contains frozen Event metadata/identities, directions,
anchors, eligibility, official filing counts, disclosure readiness, all four
per-Event outcome windows, per-metric missingness, Event and Outcome boundaries,
method versions, snapshot/revision references and the retained market-input ID.
No provider access, price processing, `execute`, `reproduce`, return method or
market snapshot loading is used by #33. Reproduction reads the same retained
#32 output and verifies its digest and equality before recomputing cohort
statistics. Source outcomes, disclosure evidence and Monitoring are unchanged.

The public deterministic seam `summarize(retained_run)` and application/API
commands are the acceptance seams. Compact statistical fixtures describe the
retained output contract; application tests also use actual isolated #32 runs.

## Population and reporting

The fixed inventory includes every retained Event. Estimates use only primary
disclosure-eligible Events with available aligned outcomes and retained ready
chambers. Unready chambers remain in flow/coverage with explicit readiness
missingness. House-only and Senate-only readiness are labeled. Event directions
come from frozen intrinsic fields and are not netted. Supported publication-year
coverage survives missing anchors; available outcomes use anchor-session years.

Every horizon reports combined, purchase/sale, ready-chamber, observed-year,
outcome-available/missing and filing-size sensitivity groups. Only the combined
20-session event-weighted aligned log mean is primary. Other horizons, strata,
medians, quartiles and IQRs support it. Filing size never excludes an Event.
Complete original official artifact counts use the pre-specified <15 / >=15
literal ticker split; partial, incomplete or ambiguous evidence is indeterminate.
Retained row/equity/security/literal/unresolved counts and their completeness and
minimum semantics remain available. No behavioral labels or amount weighting
are inferred. Frozen missing transaction dates and amount ranges are reported
separately and affect only their dependent uses.

Sample dimensions include inventory Events, analysis-available outcomes, missing
outcomes, distinct members/securities/original source filings/anchor sessions,
episodes/months, chamber counts and observed range. Distinct dependence dimensions
are counted on the observations supporting estimates; `population_dimensions`
also exposes inventory dimensions. Concentration is Event counts by member,
source filing, security, anchor session and year, ordered by identity, without
member performance rankings. Coverage dimensions and non-exclusive reason counts
are retained for every result alongside As-Of semantics, versions, boundaries
and snapshot identities.

Flow distinguishes retained market-completed windows from ready-chamber Analysis
denominators. For each horizon: Events = market-completed + market-missing;
market-completed = final denominator + readiness-blocked;
Events = final denominator + Analysis-missing. Non-exclusive reasons need not sum
to a denominator. No unavailable outcome becomes zero or a shortened window.

## Uncertainty and determinism

`cohort-analysis@2` retains its method contract, fixed cohort definitions,
thresholds, seed derivation inputs and bootstrap metadata. Seeds use canonical
JSON SHA-256's first 64 bits, stored as decimal strings to avoid JavaScript
integer precision loss. Inputs are sorted by Event identity before aggregation
or seeding. The integer-seeded Python MT19937 generator and linear `(n-1)p`
empirical percentile convention are recorded. New defaults do not change
retained reproduction; unavailable retained implementations fail explicitly.
The archived `cohort-analysis@1` implementation reproduces its original reports
and seed derivation, including its superseded empty-draw suppression behavior.
Only new v2 runs use the approved valid-replicate procedure. Advancing the method
version changes seed derivation while retaining deterministic versioned inputs.

The 10,000 member-cluster replicates sample the observed member count with
replacement. Complete member totals and Event counts reproduce full-cluster
repetition. The event-weighted replicate divides sampled cluster totals by
sampled Event counts. The member-balanced replicate averages sampled member
means equally, using the very same member draws. Both require 30 available
reporting members for intervals; point estimates do not require that threshold.

Episodes group historically resolved security, source direction and anchor
session, average within group, and receive equal weight. Anchor-open instants
determine Monday–Sunday weeks in America/New_York. The observed week range
includes empty calendar weeks. Overlapping four-week blocks are drawn with
replacement until the original week count is met, and the final block is
truncated; complete episodes in each retained sampled week are repeated.
The retained seed initializes the block-draw PRNG stream. Episode
intervals require 30 members, 30 episodes and 12 distinct anchor months in that
analyzed cohort. Empty draws have no numerical estimator and never contribute
to percentiles. They are recorded as invalid using one-based attempt indices;
the same stream continues until exactly 10,000 valid episode estimates exist.
Only zero sampled episodes makes a draw invalid; legitimate zero, negative,
positive and contradictory values are equally valid. Provenance retains the
requested valid count, total attempts, valid count, empty count, indices, seed
and derivation inputs. A fixed 50,000-attempt safeguard is retained in the method
contract. Exhaustion withholds the entire episode interval with the stable
operational reason `episode_bootstrap_draw_attempt_limit_reached`, retaining
partial attempt counts and the supported episode point. No reduced-replicate
interval is reported. Reproduction reuses the recorded method and attempt limit.

Intervals are the 2.5th and 97.5th empirical percentiles. Supporting intervals
are descriptive and unadjusted for multiple comparisons. Supported points,
distributions and concentration remain visible below thresholds. Strict positive
versus negative disagreement across supported estimates is flagged; zero has no
direction and no magnitude cutoff is used. Primary intervals containing zero
receive valid null/inconclusive language, never proof of exact zero. No p-values,
causal/alpha claims, endpoint selection, trading advice or member rankings exist.
Historical Raw/Expected/Excess Consensus remain explicitly unavailable/null.

## Persistence, APIs and presentation

`analysis_cohort_runs` appends an immutable run with method/version, population,
calculation time, source run/reference, exact source output, input digest and full
report. Every execution appends a new identity; no update/delete path exists.

- `GET /api/analysis/cohorts`: production capability and retained cohort runs.
- `POST /api/analysis/cohorts`: explicit command with `sourceRunId` only.
- `GET /api/analysis/cohorts/{id}`: retained production run.
- `GET /api/analysis/cohorts/{id}/reproduction`: verified cohort reproduction.

HTTP forces real population and rejects population/seed/horizon/threshold
overrides. Production execution requires production market readiness and
production source outcomes. Test/evaluation execution requires isolated synthetic
source readiness. Raw source and dynamic reason/identity keys are preserved at
the router boundary. The existing Analysis page adds restrained cohort tables,
independent loading/error state, flow, uncertainty, dimensions and expandable
coverage/seeds/provenance. Synthetic runs are withheld from production display.

## Limitations and verification

Retained #32 inputs do not certify the longest reliable common historical
disclosure period or its gaps. Reports therefore retain the observed range,
the five-complete-years-plus-current-year requirement, `panel_complete: false`
and an explicit exploratory/unvalidated-period label. Event presence is never
used as proof of reliable history. Provider adoption and production activation
remain outside #33; production readiness remains unavailable.

The tests cover weighting, member resampling, episode grouping, New York
weeks and block truncation/gaps, percentile goldens, threshold boundaries,
sign disagreement, deterministic seeds/row order, filing sensitivity, denominators,
field missingness, readiness isolation, null language, raw-key serialization and
reproduction without #32 recalculation.

### Initial v1 verification (2026-10-06)

- Focused #33 application/statistical/API tests: **18 passed**.
- Relevant #32/#31 regression tests: **58 passed**.
- Full backend suite on the initial v1 implementation: **218 passed**.
- Frontend render/contract tests: **9 passed**.
- TypeScript application and frontend-test checks, ESLint, Python compilation
  and production Vite build: passed.
- Source/configuration/fixture and fresh-bundle secret scans: passed.
- Capability containment tests: passed; new production modules and fresh bundle
  contain no synthetic fixture imports or identifiers.
- Requested read-only `git diff --check` and explicit whitespace checks including
  new files: passed. No Git state mutation or commit was performed.
- Standards review: **0 remaining actionable findings**.
- Spec review: **0 remaining actionable findings**. Review covered weighting,
  complete-cluster resampling, episode identity, block gaps/truncation, threshold
  leakage, deterministic ordering/seeds, post-hoc selection, denominators,
  frozen filing metadata, readiness population and forbidden #32 recalculation.

Frontend build used bundled Node 24.19. Existing large-chunk and test-client
deprecation warnings remain non-blocking. No provider was selected or activated.

### Approved v2 follow-up verification (2026-10-06)

The subsequent narrow audit identified the unspecified empty-draw suppression
policy. The explicit approved supplement above resolves that methodology blocker.

- Focused #33 statistical/application/API suite: **24 passed**.
- Relevant #32/#31 regression suite: **58 passed**.
- Full backend suite on the final v2 implementation: **224 passed**.
- TypeScript application check and Python compilation: passed.
- Changed-file secret-signature, fixture-isolation and whitespace checks: passed.
- Final scoped statistical and standards reviews: **0 blockers**.
- Exact comparison with the pre-fix implementation: the entire sparse v1 report
  is unchanged when reproduced under its retained method version.

Independent source-contract seed derivation and explicit flattened-episode
reference draws confirm the sparse-cohort regression: the original v1 seed has
86 empty attempts in the first 10,000 draws and reaches 10,000 valid estimates
after 10,088 attempts (88 empty). The v2 seed reaches 10,000 valid estimates after
10,094 attempts (94 empty). All estimates in this analytical +1 fixture equal
1, so its independently known percentile interval is `[1, 1]`. Existing varied
outcome goldens independently check cluster and episode weighting/percentiles.
Regressions also prove zero-valued outcomes stay valid, empties cannot contribute
synthetic zeros, row reversal preserves counts/intervals, the safeguard retains
failure counts and supported points, and both versions reproduce from retained
#32 outputs. No Git operations were performed in this follow-up.

### Acceptance audit

| #33 acceptance criterion | Implemented behavior / evidence |
|---|---|
| 20 sessions sole primary; 1/5/60 supporting | Fixed method contract and primary flag only for combined 20-session event-weighted mean; all horizons retained. |
| House-only readiness; short periods exploratory | Retained ready-chamber population gate, chamber label, observed range, five-complete-years-plus-current-year requirement and unvalidated/exploratory coverage. Mixed-chamber regression verifies no Senate leakage. |
| Always report supported primary/member/episode points | All three estimates are produced from available eligible observations independently of interval thresholds; unavailable values remain null. |
| Approved interval thresholds | Every analyzed cohort/horizon separately requires 30 members; episode interval additionally requires 30 episodes and 12 anchor months. Boundary tests cover 29/30 and 11/12. |
| Approved empty episode draws | Exactly 10,000 valid estimates, same PRNG stream, explicit empty-attempt recording, no synthetic values, 50,000-attempt safeguard with stable unavailability reason; method/version/limit and all counts retained and reproduced. |
| Strict sign disagreement; no magnitude binary | Any supported positive and negative estimate flags disagreement; zero is neutral; tiny-sign regression verifies no magnitude cutoff. |
| Dimensions, coverage, missingness, versions/boundaries/snapshots | Per-result sample/inventory dimensions, distributions, concentration, reconciled flow, non-exclusive reason counts and exact provenance; source output and seeds retained. |
| Filing size sensitivity only, indeterminate separate | Original official artifact counts use literal-ticker split only when complete; otherwise indeterminate. Primary cohort unchanged; no behavioral labels. |
| Null/negative/contradictory/small/unavailable valid | Controlled neutral interpretation and explicit estimate/interval availability, null-language and frontend tests; no rankings, recommendations or causal claims. |
| Historical Consensus unavailable | Explicit unavailable Raw/Expected/Excess values and deferred reason in reports and presentation. |

Additional contract checks: both 10,000-replicate methods have independent
worked/reference goldens; row reversal preserves report and seeds; original v1
reproduction survives a changed default; repeated commands append distinct runs;
test/evaluation output cannot cross production query/execution/HTTP boundaries;
and a market-method guard proves execution/reproduction never recalculates #32
returns.

Changed files: `server/cohort_analysis.py`, `server/db/schema.sql`,
`server/routers/analysis.py`, `server/tests/test_cohort_analysis.py`,
`server/tests/test_cohort_analysis_api.py`, `src/data/analysisTypes.ts`,
`src/data/useAnalysis.ts`, `src/detail/AnalysisPage.tsx`,
`src/detail/CohortResults.tsx`, `frontend-tests/capabilities.test.ts`,
`docs/specs/cohort-empty-bootstrap-33.md`, and this file.

Suggested commit: `feat(analysis): report deterministic cohorts and uncertainty (#33)`.
