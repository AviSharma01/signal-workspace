# Signal V2 Specification

Status: Final approved implementation specification. Approved by the driving developer on 2026-10-01 for implementation decomposition. Approval does not certify disclosure-source or market-data operational readiness.

## Problem Statement

Signal needs one coherent V2 contract for determining whether Congressional trading disclosure Events contain reproducible, statistically measurable information and for monitoring verified recent Events without overstating what the available evidence can support.

The existing application is a V1 prototype, not a V2 authority. The approved Wayfinder decisions establish the required provenance, identity, point-in-time, lifecycle, recovery, missingness, no-advice, and evidence-boundary rules, but they intentionally leave the exact event-study method and the detailed responsibilities of the shared evidence spine, Analysis, Monitoring, investigation, graph, and application boundaries to this specification.

V2 must remain useful when results are null, evidence is incomplete, an explanation is unavailable, an LLM is absent, or a capability is blocked. It must not imply that historical coverage is complete, that an available source is fresh, that an observed ticker is permanent security identity, that a later correction was known earlier, or that missing market data means a zero return.

Market-data readiness is currently blocked under the approved minimum contract. No provider, compatible fallback, provider-specific behavior, or bounded revision-refresh policy is selected. Historical Raw Consensus, Expected Consensus, and Excess Consensus are unavailable and deferred from current V2. The q language is not adopted in current V2. These conditions must be represented as capability states, not hidden behind partial results or placeholder values.

## Solution

Build V2 around a local-first shared evidence/data spine that preserves source material and observations, derives versioned interpretations without overwriting evidence, and supplies deterministic application services for Event identity, use-specific eligibility, Watch Event lifecycle, replay, Analysis, Monitoring, and bounded investigation.

Analysis will implement a pre-specified daily event study only after the disclosure and market-data readiness gates are satisfied. The primary study uses the first regular-session open strictly after supported public availability, a fixed broad-market benchmark instrument, deterministic total-return semantics, a 20-session primary outcome, explicit supporting horizons, direction-aware treatment of purchases and sales, dependence-aware uncertainty, complete missingness accounting, and strict prevention of point-in-time leakage. Null, contradictory, and small-sample results remain first-class outputs.

Monitoring will admit verified Watch Events independently of market-data availability, apply the approved publication-based 30-calendar-day lifecycle, preserve actual system-observation times, reevaluate deterministically, recover without backdating, and expose each capability separately. Market observations, market anomaly detection, and market-triggered investigation remain unavailable until the market-data contract is satisfied.

Investigations will be bounded, read-only with respect to source/evidence data, evidence-cited, auditable, optional with respect to model availability, structurally no-advice, and allowed to conclude unexplained. The graph remains a Monitoring and navigation surface. It does not calculate Analysis results, establish identity, or replace the evidence spine.

The highest acceptance seam is the deterministic application boundary: retained source evidence and recorded observations enter once, and versioned Events, eligibility decisions, Watch Event lifecycle history, capability status, Analysis run manifests/results, and validated Findings are observed through application APIs. Lower-level tests support this seam but do not substitute for it.

## User Stories

1. As a researcher, I want every conclusion traceable to retained evidence, so that I can audit what the system knew and why it produced a result.
2. As a researcher, I want official disclosure artifacts to be the evidentiary foundation, so that aggregator convenience does not silently become source authority.
3. As a researcher, I want official and aggregator representations preserved separately, so that discrepancies remain visible.
4. As a researcher, I want unchanged raw source values retained alongside normalized values, so that transformations can be inspected and rerun.
5. As a researcher, I want extraction and normalization versions recorded, so that source changes are distinguishable from processing changes.
6. As a researcher, I want identical reported row occurrences preserved separately, so that value equality does not erase real occurrences.
7. As a researcher, I want repeated retrieval of unchanged content recorded as another observation rather than another transaction, so that retries remain idempotent.
8. As a researcher, I want changed artifacts versioned without assuming they are amendments, so that content changes are not overinterpreted.
9. As a researcher, I want corrections applied only within their supported scope, so that later evidence does not rewrite unrelated fields.
10. As a researcher, I want candidate and verified cross-source relationships distinguished, so that unverified matches never authorize deduplication.
11. As a researcher, I want member and security identities resolved from evidence and scoped historically, so that present-day names and tickers do not leak backward.
12. As a researcher, I want malformed and ambiguous content retained with explicit status, so that parse failures are not silently dropped or repaired.
13. As a researcher, I want one Event per reported transaction occurrence, so that filings, members, and securities remain groupings rather than substitutes for event identity.
14. As a researcher, I want use-specific eligibility reasons, so that an Event can remain retained while a particular measurement is unavailable.
15. As a researcher, I want public-information and system-observation As-Of perspectives kept separate, so that historical Analysis and operational replay make defensible claims.
16. As a researcher, I want publication timestamps, publication dates, retrieval times, and filing dates represented according to what each proves, so that the system never fabricates temporal precision.
17. As a researcher, I want date-only publication evidence to become eligible only after the supported source-local day ends, so that a fabricated midnight or market-open timestamp cannot leak information.
18. As a researcher, I want the primary Event Anchor to be the first applicable regular-session open strictly after supported availability, so that returns begin after the disclosure could have been known.
19. As a researcher, I want Event-intrinsic State frozen at the Event's supported public-availability boundary, so that later corrections do not rewrite the original study input.
20. As a researcher, I want Pre-session Contextual State limited to evidence available strictly before the anchor open, so that outcomes and same-open facts cannot become predictors.
21. As a researcher, I want separately versioned historical recomputations, so that improved processing can coexist with the results actually produced earlier.
22. As a researcher, I want corrected-retrospective views labeled with later As-Of Boundaries, so that they cannot be confused with point-in-time results.
23. As a researcher, I want primary Analysis limited to official, identity-resolved, publication-anchored Events, so that exploratory records do not support authoritative conclusions.
24. As a researcher, I want House-only Analysis allowed when Senate readiness is inadequate, so that defensible limited coverage is preferred to a false complete panel.
25. As a researcher, I want Analysis labeled exploratory when it lacks five complete calendar years plus the current year, so that the approved minimum is not silently weakened.
26. As a researcher, I want the benchmark instrument and return calculation fixed before outcomes are inspected, so that the method cannot be optimized for an exciting result.
27. As a researcher, I want the primary outcome window fixed at 20 regular sessions, so that the main result is not selected after comparing horizons.
28. As a researcher, I want 1-, 5-, and 60-session supporting windows, so that immediate, weekly, and approximately quarterly patterns are visible without replacing the primary endpoint.
29. As a researcher, I want purchase and sale outcomes reported separately, so that opposite source directions are not hidden by pooling.
30. As a researcher, I want one direction-aligned primary estimate, so that the study has a single pre-specified main test of directional information.
31. As a researcher, I want raw security, benchmark, and benchmark-relative returns reported together, so that abnormal results remain interpretable.
32. As a researcher, I want unresolved corporate actions to make only the dependent return unavailable, so that Signal never invents continuation prices or terminal returns.
33. As a researcher, I want missing prices and incompatible sessions reported rather than filled, so that missing outcomes are never turned into zero or shortened windows.
34. As a researcher, I want complete eligibility and measurement flow counts, so that every reduction in sample size is visible.
35. As a researcher, I want sample sizes by Events, members, securities, filings, anchor sessions, and outcome availability, so that row counts are not mistaken for independent evidence.
36. As a researcher, I want uncertainty clustered by reporting member, so that repeated Events from one member do not appear independent.
37. As a researcher, I want the primary, member-balanced, and security-session episode estimates reported whenever supported, with directional disagreement flagged, so that shared outcomes and prolific reporters cannot silently drive the result.
38. As a researcher, I want small cohorts reported descriptively without unstable inferential claims, so that sparse data is not overstated.
39. As a researcher, I want null and contradictory results preserved, so that study success does not depend on finding a positive effect.
40. As a researcher, I want filing-size measures reported without behavioral labels, so that size does not become an unsupported proxy for discretion or passivity.
41. As a researcher, I want otherwise eligible Events retained regardless of filing size, so that an unvalidated bulk cutoff does not define the primary population.
42. As a researcher, I want the legacy 15-literal-ticker threshold used only as a declared sensitivity with an indeterminate group, so that its influence can be measured without making it a default or behavioral classifier.
43. As a researcher, I want historical Raw, Expected, and Excess Consensus shown as unavailable, so that deferred features never appear as zero or proxies.
44. As an operator, I want source availability and freshness reported separately, so that a reachable stale source does not imply current coverage.
45. As an operator, I want daily disclosure discovery and catch-up after downtime, so that local-first operation can recover without pretending it was always on.
46. As an operator, I want unverified aggregator records retained as discovery candidates, so that they can assist verification without becoming Watch Events.
47. As an operator, I want verified Watch Events admitted without market observations, so that disclosure lifecycle monitoring is independent of the market-data blocker.
48. As an operator, I want admission, active eligibility, capability availability, and check outcomes represented separately, so that one status never implies the others.
49. As an operator, I want a 30-calendar-day publication-based active window with approved timezone and DST behavior, so that active eligibility is deterministic.
50. As an operator, I want unknown or interval-valued publication age handled conservatively, so that uncertainty never becomes a fabricated active status.
51. As an operator, I want downtime never to restart or extend recency, so that recovery does not make old disclosures newly public.
52. As an operator, I want official withdrawal, unresolved evidence, failed admission criteria, and expiry retained as separate reasons, so that lifecycle history remains precise.
53. As an operator, I want Watch Event reevaluation at admission, new evidence, startup, expiry, and before active-only actions, so that stale stored state cannot authorize work.
54. As an operator, I want unchanged reprocessing to avoid duplicate admissions and transitions, so that retries and replay are safe.
55. As an operator, I want committed lifecycle transitions distinguishable from failed attempts, so that recovery does not invent completed history.
56. As an operator, I want market-data capability explicitly unavailable until its contract passes, so that price features do not partially activate against unsupported data.
57. As an operator, I want each unavailable capability to carry stable reasons and prerequisites, so that the next action is auditable.
58. As an investigator, I want a bounded evidence budget and explicit As-Of Boundary, so that investigations cannot search indefinitely or use ineligible facts.
59. As an investigator, I want read-only evidence tools, so that interpretation cannot modify its own source record.
60. As an investigator, I want every claim and counterclaim linked to eligible evidence, so that narrative confidence cannot replace provenance.
61. As an investigator, I want unexplained to be a valid outcome, so that the system does not manufacture a story.
62. As an investigator, I want model-dependent investigation to degrade to unavailable or incomplete, so that deterministic core operation does not require an LLM.
63. As a reviewer, I want Findings validated and persisted only through application-owned paths, so that agent output cannot bypass lifecycle, schema, or no-advice checks.
64. As a reviewer, I want no-advice enforced in structured fields and free text before display, so that prompts are not the only safety control.
65. As a reviewer, I want investigation selection evaluated against an independent target and baseline, so that more agent activity is not mistaken for better selection.
66. As a user, I want the graph to navigate Watch Events, evidence, related entities, anomalies, and Findings, so that I can inspect Monitoring context.
67. As a user, I want graph relationships to declare their basis and uncertainty, so that visual proximity does not imply verified identity or causality.
68. As a user, I want Analysis in tables and charts with outcomes, uncertainty, coverage, and sample sizes, so that the graph is not mistaken for the analytical engine.
69. As a user, I want unavailable and conditional states visible on every affected surface, so that missing capabilities cannot look like empty valid results.
70. As a developer, I want provider-specific behavior behind evidence-preserving adapters, so that domain calculations remain deterministic and provider-independent.
71. As a developer, I want frontend access only through application APIs, so that browser code cannot bypass provenance or expose secrets.
72. As a developer, I want deterministic method and policy versions on outputs, so that replay and comparison are reproducible.
73. As a developer, I want demo and evaluation fixtures isolated from real data, so that tests cannot contaminate production evidence.
74. As a developer, I want secrets excluded from frontend code, committed configuration, fixtures, and logs, so that local-first operation remains safe.
75. As a maintainer, I want Python retained for current V2 unless a later measured boundary approves q, so that the design does not introduce an unmeasured operational split.

## Implementation Decisions

### 1. Authority, scope, and capability model

- The approved Wayfinder resolutions and project invariants are normative inputs. V1 code and historical specifications are migration context only.
- V2 exposes capability availability as `available`, `conditional`, or `unavailable`, with stable reason codes, human-readable detail, evaluated time, governing contract/policy version, and unmet prerequisites. Capability availability is a separate axis from the state of a request or returned result. An empty result is never used to represent an unavailable capability.
- Readiness is use-specific and chamber-specific where necessary. Disclosure retention, primary Analysis eligibility, Watch Event admission, active eligibility, market outcome measurement, anomaly detection, and investigation may have different states for the same Event.
- Core deterministic operation does not depend on a paid data source, an API model, a local model, or q.
- q adoption is deferred. Current V2 uses the existing Python application boundary unless a later approved, measured proposal establishes a narrow useful q boundary and independent numerical parity criteria.

### 2. Shared evidence/data spine

- The spine is the sole authoritative route from source retrieval to user-facing Event, Watch Event, Analysis, Monitoring, and Finding read models.
- It preserves Source Filings, Retained Filing Artifacts, Filing Artifact Versions, Filing Retrieval Observations, Reported Row Occurrences, raw official and aggregator evidence, extracted representations, normalized fields, candidate and verified occurrence relationships, resolved member/security identities, availability evidence, Events, use-specific eligibility assessments, Watch Event lifecycle history, market-data snapshots when available, Analysis runs/results, investigation runs, and Findings.
- Raw source material is immutable. Corrections, withdrawals, relationships, interpretations, eligibility assessments, and derived values are appended or versioned; they do not overwrite the evidence they interpret.
- Every derived record identifies its input evidence, applicable As-Of perspective and boundary, transformation/method/policy version, computation time, and status. Market outcomes additionally identify the Outcome Boundary and Market-data Snapshot.
- Source availability, source freshness, coverage, parsing success, identity resolution, and use-specific eligibility are separate assessments.
- Demo and evaluation data use physically or logically isolated storage and cannot enter real discovery, Analysis, Monitoring, or investigation populations.

### 3. Ingestion and normalization boundaries

- House discovery uses official annual/index artifacts and separately retrieves original official filings. Kadoa may assist discovery, extraction, historical coverage, and cross-checking but remains separately attributed. Senate uses official artifacts where validated access permits; aggregator sources are supporting discovery only.
- No chamber is operationally ready until bounded validation covers minimum history/gaps, original-artifact retrieval, amendment/backfill behavior, retention permission, daily discovery, downtime catch-up, and reconciliation of older additions/changes.
- Ingestion persists the retrieved source representation and retrieval observation before derived interpretation. Parse or normalization failure never prevents raw preservation.
- Repeated retrieval of identical content creates a new retrieval observation but not a new artifact version or Event. Changed content creates a new artifact version but does not by itself establish amendment status, row correspondence, or a new transaction.
- Source filing identity, artifact/version identity, retrieval identity, and row-occurrence identity are distinct. Two identical rows remain two occurrences. Position and value equality alone never establish cross-version or cross-source identity.
- Official and aggregator representations never overwrite one another. Candidate occurrence relationships cannot deduplicate; only verified relationships can establish a shared Event.
- Extracted text records artifact/version, method/version, and relevant extraction time. Normalization covers date parsing, amount parsing, transaction direction mapping, ticker normalization, and similar transformations while retaining original source text.
- Date-only source values remain dates. Reported negative disclosure latency remains visible. Unsupported values remain unresolved rather than repaired.
- Resolved member and security identities are evidence-backed and historically scoped. Ambiguous identity remains explicit; present-day ticker mappings cannot be applied backward without eligible evidence.
- Discovery runs at least daily while Signal is running. Startup and recovery reconcile missed and older changed filings. Fetch success, last successful retrieval, latest source coverage, and source freshness are recorded separately.

### 4. Event identity and temporal contract

- One Event corresponds to one reported transaction occurrence. Verified representations of the same occurrence link to that Event. Filing, member, and security collections are derived views.
- Aggregator-only records may be Unverified Discovery Candidates. They are not Watch Events and are ineligible for primary Analysis until official evidence and remaining checks succeed.
- Availability evidence retains its source, artifact/version, precision, timezone/calendar meaning, and claim. Supported exact publication time, supported publication date, retrieval time, and reported filing date are never treated as interchangeable.
- An exact supported publication instant establishes an exact availability boundary. A supported date establishes an interval within the source-local day and becomes conservatively eligible only after that day ends. Retrieval proves availability no later than retrieval. A filing date alone does not prove public availability.
- Primary Analysis uses Public-information As-Of. Monitoring replay and operational audit use System-observation As-Of. Later publication evidence never backdates local observation.
- The primary Event Anchor is the first applicable regular trading-session open strictly after the supported availability boundary. Exact publication at an open uses the next regular-session open. Calendars include holidays, early closes where relevant, and exchange timezones.
- Event-intrinsic State is frozen at supported publication availability. Pre-session Contextual State includes only eligible evidence strictly before the derived anchor open. Evidence exactly at or after the open is excluded from predictors, eligibility, cohorts, and event selection.
- Amendments and corrections remain separately timed evidence on the same Event when correspondence is established. They do not reset the original anchor or retroactively repair earlier eligibility. New occurrences create new Events.
- Historical recomputation may reinterpret evidence that was eligible at the original boundary using a new method version, while preserving the earlier result. Later evidence requires a separately labeled corrected-retrospective view with a later As-Of Boundary.

### 5. Primary Analysis population and cohorts

- The target population is House and Senate members' purchases and sales of individual publicly traded equities. All raw disclosure records remain retained regardless of eligibility.
- Primary disclosure eligibility requires retrieved official evidence, supported occurrence identity, interpretable purchase or sale direction, individual-equity classification, sufficient resolved member identity, historically scoped security/listing identity, supported publication availability, and no unresolved duplicate relationship that makes analytical counting ambiguous.
- Primary market-outcome eligibility additionally requires a USD-denominated U.S.-listed instrument with regular-session times compatible with the benchmark, a complete validated session calendar, required market observations and corporate actions, and satisfied market-data semantics. Events outside this measurement scope remain retained with the dependent outcome unavailable.
- The main historical study uses the longest reliable common period that contains at least five complete calendar years plus the current year. Prefer longer defensible STOCK Act-era coverage. If only one chamber meets readiness, a chamber-limited study is allowed and labeled. A shorter period is exploratory only.
- The primary cohort contains all otherwise eligible Events regardless of filing size. Purchases and sales remain distinct source directions and are never netted within a filing, member, security, or window.
- Mandatory cohort outputs are: combined direction-aligned primary cohort; purchase cohort; sale cohort; House and Senate strata when each is ready; calendar-year strata; and outcome-availability/missingness strata.
- Filing-size reporting retains total row occurrences, interpretable in-scope equity occurrences, distinct resolved equity securities, literal source ticker strings for diagnostics, unresolved counts, completeness status, and defensible ranges/minima.
- The pre-specified filing-size sensitivity compares filings with fewer than 15 versus at least 15 distinct literal source ticker strings, with incomplete/indeterminate filings separate. It is a legacy threshold sensitivity only, not a primary exclusion, security-count substitute, or behavioral/discretion classifier.
- Contextual adviser/control/intent statements remain scoped attributed evidence. No behavioral cohort is formed from filing size or missing contextual statements.
- Historical Raw Consensus, Expected Consensus, Excess Consensus, peer-count windows, baseline models, and proxies are unavailable and excluded from current V2 predictors and cohorts.

### 6. Benchmark and return semantics

- The fixed primary benchmark instrument is the SPDR S&P 500 ETF Trust (SPY), resolved through its historically scoped security and listing identity. This selects a benchmark, not a market-data provider.
- A market-data source may supply the required security and SPY observations only after it satisfies the approved minimum market-data contract. Provider-adjusted prices alone do not satisfy the calculation contract.
- Required inputs are unadjusted regular-session OHLCV, separately attributed corporate actions, validated exchange-session calendars, historically scoped listing mappings, field/unit/currency/session semantics, source provenance, retrieval observations, and retained data revisions.
- For each Event, the anchor session is session 1. Outcome windows contain 1, 5, 20, or 60 benchmark-compatible regular sessions, including the anchor session. The 20-session window is the single primary horizon; 1, 5, and 60 are supporting horizons. No +7/+30/+90 default is used.
- Each window begins at the security's regular-session open on the anchor session and ends at its regular-session close on the final included session. The Outcome Boundary is that final close. A window is not shortened when a required observation is absent.
- The security gross total-return factor begins with the anchor-session close divided by the anchor-session open. On a common split-normalized share basis, for a `k`-session window it is the anchor close/open factor multiplied by each later session's `(close + ex-date cash distribution) / prior close` factor through session `k`. This compounds cash distributions as if reinvested at the ex-date session close. A distribution with an ex-date on the anchor session is excluded because the position begins at that session's open. Splits change share basis, not economic return.
- The benchmark gross total-return factor is computed by the same convention over the same included session dates. If security and benchmark sessions/timestamps cannot be aligned without approximation, the measurement is unavailable.
- Non-cash distributions, mergers, spin-offs, delistings, listing changes, terminal events, ambiguous actions, or unresolved currency/identity semantics make the affected window unavailable unless a later approved deterministic treatment is supported by sufficient evidence. Signal never invents a continuation or terminal return.
- The benchmark-adjusted log return is the natural log of the security gross factor divided by the benchmark gross factor. The equivalent compounded relative return is its exponential minus one. Both are deterministic outputs; the log form is used for aggregation and uncertainty.
- Purchase direction is +1 and sale direction is -1. The primary Event outcome is direction multiplied by benchmark-adjusted log return. Positive values mean movement aligned with the disclosed direction; negative values mean movement against it. This is a research convention, not a recommendation, claim of causality, personal direction, conviction, or feasible trading return.
- Every result reports the raw security total return, benchmark total return, benchmark-adjusted return, direction-aligned return where applicable, input snapshot, method version, and all unavailable reasons.

### 7. Estimands, dependence, uncertainty, and small samples

- The single primary estimand is the event-weighted mean direction-aligned benchmark-adjusted log return at 20 sessions across the primary cohort.
- Required supporting estimates are the purchase and sale event-weighted means at 20 sessions, the combined and direction-specific estimates at 1, 5, and 60 sessions, medians and interquartile ranges, chamber/year strata, and coverage counts. Supporting estimates do not replace the primary endpoint.
- The primary 95% confidence interval uses a deterministic 10,000-replicate reporting-member cluster bootstrap. Each replicate samples the observed number of distinct resolved reporting members with replacement and includes all eligible Events, filings, securities, and anchor sessions belonging to each sampled member, repeating a member's complete cluster when that member is sampled more than once. The interval is the empirical 2.5th and 97.5th percentiles of the replicate estimates. The pseudorandom seed must be deterministic for the same method version, cohort, horizon, and ordered inputs; the seed and its derivation inputs are retained in the run manifest. No particular hashing scheme is required.
- The member cluster is the primary dependence unit because Events within a filing and repeated Events from a member are not independent. The output also reports concentration by member, filing, security, anchor session, and calendar period.
- A mandatory member-balanced sensitivity first averages eligible Event outcomes within each member and then averages equally across members. This shows whether prolific reporters dominate the event-weighted result. When its inferential threshold is met, its 95% interval uses the same member resamples and empirical percentile construction as the primary interval.
- A mandatory shared-outcome sensitivity groups Events by historically resolved security, source direction, and anchor session, averages within each group, and estimates an equally weighted security-direction-session episode mean. Anchor weeks are Monday-through-Sunday calendar weeks in America/New_York. Its uncertainty draws overlapping four-week blocks with replacement from the chronologically ordered observed week range until at least the original number of weeks is represented, truncates the final block to that count, retains complete episodes in each sampled week, and uses 10,000 replicates with the same deterministic seed and empirical percentile convention.
- When at least one eligible Event outcome exists, always report the primary event-weighted estimate. When at least one eligible member outcome exists, always report the member-balanced estimate. When at least one eligible security-direction-session episode exists, always report the episode estimate. Report each supported estimate with its interval when the applicable inferential threshold is met, its sample sizes, and any availability limitation. Explicitly flag directional disagreement when any supported estimate is strictly positive and another is strictly negative. An estimate equal to zero has no direction for this flag. Do not classify magnitude differences with a binary threshold; preserve the estimates so users can inspect those differences directly. No preferred estimate is selected after inspecting outcomes.
- Inferential intervals and claims require at least 30 distinct reporting members in the analyzed cohort. The shared-outcome interval additionally requires at least 30 episodes spanning at least 12 distinct anchor months. Below a threshold, point estimates, distributions, concentration, and coverage are reported as descriptive small-sample results without a confidence interval or statistically distinguishable claim.
- The primary estimate is described as statistically distinguishable from zero only when its pre-specified 95% interval excludes zero. An interval including zero is a valid null/inconclusive result, not proof of exact zero or no information.
- No p-value, alpha claim, causal claim, trading-performance claim, or post-hoc choice among horizons/cohorts is required. Supporting intervals are descriptive and explicitly unadjusted for multiple comparisons.
- Method choices, thresholds, cohort definitions, and seeds are versioned before relevant outcomes are inspected. A method change creates a new Analysis run and does not overwrite prior results.

### 8. Missingness and result reporting

- Missingness is field- and use-specific. Missing amount does not exclude a direction-resolved Event from the primary return study. Unknown transaction date may block latency measures without blocking a supported publication-time study. Unresolved security identity blocks market outcomes, not evidence retention.
- Missing market observations, required semantics, corporate actions, benchmark compatibility, or session alignment make the affected outcome unavailable. No return is imputed, set to zero, forward-filled, backfilled, substituted from another security, or computed over a shorter window.
- Every Analysis run publishes a flow table from retained row occurrences through Events, official verification, each disclosure eligibility requirement, market-outcome eligibility, and each completed outcome window. Reasons are non-exclusive and both per-reason and final denominators are shown.
- Coverage is reported by chamber, calendar year, source role, purchase/sale direction, filing-size completeness, and relevant identity/availability/market-data failure reason. Uneven coverage is never labeled a complete panel.
- Every statistical output includes Event count, distinct members, securities, source filings, anchor sessions, episodes, covered time range, chamber coverage, outcome-available count, missing count, method version, As-Of definition, Outcome Boundary, and Market-data Snapshot identity.
- Null, negative, contradictory, directionally disagreeing, small-sample, and unavailable results use neutral language. No result is ranked or framed as a buy/sell/hold signal.

### 9. Market-data readiness and conditional Analysis

- Market-data readiness remains unavailable at specification publication. No provider, fallback, provider-specific behavior, or revision-refresh policy is selected.
- A candidate becomes usable only after independent evidence validates every minimum-contract requirement: historical coverage, retention rights, identity/listing joins, session calendars/timezones, OHLCV and corporate-action semantics, currency/units, provenance, daily acquisition, catch-up, gaps, changed historical bars, terminal events, source compatibility where fallback is proposed, and deterministic numerical correctness.
- Acceptance cases include ordinary sessions, holidays, early closes, DST/timezone boundaries, missing bars, ticker rename/reuse, listing changes, splits, cash and non-cash actions, mergers, spin-offs, delistings, source disagreement, and later bar revisions.
- Required workload evidence measures backfill, daily acquisition/catch-up, revision refresh, Event-to-session and security-resolution joins, representative outcome computation, request counts, elapsed time, memory, storage, and reproducibility. It does not select q.
- Until readiness passes, historical event-study results, benchmark-adjusted outcomes, market anomaly detection, market-dependent Monitoring, and market-triggered investigation are explicitly unavailable. Disclosure-only eligibility/coverage reports may be available when their own source gates pass.

### 10. Watch Event persistence, lifecycle, recovery, and replay

- Admission requires an Event with official evidence, established occurrence identity, interpretable in-scope direction, required member/security identity, sufficient temporal evidence for System-observation Monitoring, and recorded actual discovery, verification, and admission times. Market data is not an admission requirement.
- Evidence standing, continued admission-criteria satisfaction, recency, active eligibility, capability availability, check outcomes, source freshness, and blocking reasons are separate values rather than one combinatorial state.
- Active eligibility requires supported non-withdrawn evidence, continued satisfaction of all admission criteria, and qualifying recency. Unknown publication age or expiry uncertainty can permit admission while withholding active-only uses.
- The active window is 30 calendar dates anchored to supported original public availability under America/New_York policy time. For exact instants, convert and preserve local clock time across the 30-date addition. Active evaluation is strictly before expiry. At expiry it ends. Ambiguous expiry uses the earlier occurrence; nonexistent local time uses the first valid instant at or after nominal expiry.
- Date-only/interval evidence is evaluated over every supported publication time. Definitely within may be active; definitely outside is expired; a straddling interval withholds active eligibility and records uncertainty. No exact publication or expiry instant is invented.
- Discovery, admission, downtime, corrections, reinstatement, and later evidence never restart or extend the publication clock. Old Events may be admitted after expiry without becoming active.
- Official withdrawal, unresolved standing, conclusive failure of a required criterion, expiry, and other blockers preserve the Watch Event and history. Reinstatement requires newly observed admissible official evidence and reevaluation under the original clock.
- Reevaluation occurs at admission, relevant new evidence, startup/recovery, known expiry while running, and immediately before active-only actions. Displays distinguish the last persisted assessment from a current evaluation and qualify stale assessments.
- Retrieval observations are append-only. Reprocessing unchanged evidence creates no duplicate Event, Watch Event, admission, or lifecycle transition. Meaningful changes to evidence standing, criteria, recency, active eligibility, reasons, or supported expiry are persisted even if the active boolean is unchanged.
- Application-owned persistence atomically records each committed admission or lifecycle transition with evidence references, policy version, actual evaluation time, resulting assessment, and reasons. Failed or uncommitted attempts are not completed history.
- Recovery replays committed evidence/observations and reevaluates at actual current time. It records when an overdue change was observed/persisted, not a fabricated transition during downtime. Committed transitions are never repeated.
- Replay distinguishes: observations and outputs actually recorded at the historical time; deterministic reproduction of those outputs from the same versions; historical recomputation using evidence eligible at that boundary; and corrected-retrospective views using later evidence.

### 11. Monitoring responsibilities

- Monitoring owns ongoing disclosure discovery status, Unverified Discovery Candidates, verified Watch Event admission, lifecycle assessment, source freshness, capability/check status, deterministic anomaly records, bounded investigation orchestration, and operational history.
- Minimum Monitoring remains deterministic and usable without an LLM. It does not claim that an active Watch Event is fully observable or successfully checked.
- Non-market disclosure/evidence anomaly implementation is deferred until concrete deterministic criteria are separately approved and versioned. Until then, source disagreements and lifecycle evidence changes remain available through their ordinary evidence and lifecycle records rather than being promoted to Anomalies. An anomaly is an observation, not an explanation.
- Market-price, return, volatility, volume, benchmark, and market-dependent investigation triggers are unavailable until market-data readiness passes and their deterministic baselines/thresholds are separately specified before use.
- Monitoring never turns retrieval recency into publication recency, never invents checks during downtime, and never uses unverified candidates as Watch Events.

### 12. Bounded investigation contract

- An investigation begins from an explicit Event, Watch Event, or deterministic anomaly plus a declared System-observation or Public-information As-Of Boundary, trigger version, eligible evidence set, and capability snapshot.
- Investigation tools are read-only with respect to source/evidence data and have no external side effects. Any approved external retrieval occurs through application-owned evidence adapters before it becomes tool-visible.
- Each run has predeclared limits on steps and elapsed time, plus model/API spend when a paid model is used. Those are the minimum initial budgeting controls; add evidence-item, byte, or other quota dimensions only after measured need. Exhaustion yields incomplete or unexplained, not invented evidence. Optional API-model experiments remain within approved cost ceilings; core operation remains model-independent.
- Tools return evidence references, provenance, availability/observation times, and applicable eligibility. The investigator cannot silently widen its As-Of Boundary or use future market outcomes in a historical interpretation.
- A Finding contains the trigger and run identity, bounded As-Of Boundary, concise outcome category, hypotheses considered, supported claims, counterevidence, unresolved questions, evidence citations, confidence with basis, limitations/missingness, capability limitations, review status, no-advice validation status, method/model version, and actual creation time.
- `unexplained`, `insufficient eligible evidence`, `capability unavailable`, and `budget exhausted` are valid outcomes. Confidence is not a substitute for evidence.
- The application validates structure, citations, evidence eligibility, allowed outcome categories, and no-advice constraints before persisting or displaying a Finding. Free text is checked in addition to structured advice fields. Invalid output is rejected or held for review through an explicit application path.
- Investigation-selection quality is evaluated against independently judged targets and a declared baseline. More runs, more Findings, longer narratives, or greater confidence are not success metrics. If no defensible independent target exists, the limitation is reported.

### 13. Graph and navigation responsibilities

- The graph is a Monitoring/navigation projection over application APIs. It may represent Events, Watch Events, companies/securities, members, source filings/evidence, deterministic anomalies, and Findings when those records exist.
- Every relationship declares its type and evidence basis. Candidate relationships are visually and semantically distinct from verified relationships. Visual proximity, edge existence, or cluster layout never establishes identity, causality, direction, consensus, or statistical independence.
- The graph exposes lifecycle status, recency uncertainty, source freshness, capability availability, check outcomes, and blocking reasons without merging them into one status.
- Graph actions navigate to evidence, Event/Watch Event history, Monitoring context, Analysis results, or Findings. The graph does not compute financial/statistical metrics, control eligibility, persist evidence directly, or replace Analysis tables/charts.
- This specification does not redesign layout, styling, animation, or interaction. Existing graph implementation is reused or changed only through later scoped implementation work.

### 14. Analysis responsibilities

- Analysis owns historical eligibility/coverage reports, declared cohorts, event anchors, market-outcome computations, benchmark adjustment, uncertainty, dependence sensitivities, missingness, sample sizes, null-result reporting, run manifests, and versioned recomputation.
- Deterministic application code performs all financial/statistical calculations. LLMs may interpret already computed evidence but cannot manufacture returns, cohorts, confidence intervals, anomalies, or significance.
- Analysis presentation uses clear tables/charts and always pairs estimates with coverage, uncertainty, sample sizes, method version, and availability state.
- Analysis does not own Watch Event lifecycle, current source health, operational scheduling, investigation persistence, or graph layout.

### 15. API and domain boundaries

- The services below are logical responsibility boundaries, not a requirement to create a separate module, process, table, or persistence abstraction for every named service or domain record. Implementation should use the fewest concrete seams that preserve these contracts.
- Source adapters retrieve official and supporting source representations and return bytes/responses plus source/retrieval metadata. They do not emit authoritative Events directly.
- Extraction/normalization derives versioned representations from retained artifacts. It does not overwrite raw evidence or decide universal validity.
- Identity and temporal services establish candidate/verified relationships, resolved identities, availability evidence, Event Anchors, and use-specific eligibility with explicit reasons.
- A lifecycle service deterministically evaluates Watch Event admission/recency/active eligibility from persisted evidence, policy version, and evaluation time. Persistence is application-owned.
- A market-data adapter boundary is defined but disabled until a provider passes the approved contract. Provider responses never flow directly to frontend or study calculations without retained provenance and normalized semantics.
- The Analysis service consumes immutable/versioned evidence and market snapshots, produces run manifests and results, and cannot mutate source evidence or Monitoring history.
- Investigation orchestration supplies read-only eligible evidence, enforces budgets, validates output, and persists run metadata/Findings through explicit application commands.
- Query APIs expose evidence provenance, Events and eligibility, Watch Events and lifecycle history, capability status, Analysis runs/results, anomalies, investigation runs, and Findings. Mutation APIs are limited to explicit application-owned ingestion, verification/admission, lifecycle evaluation, Analysis execution, and validated Finding persistence.
- Frontend code consumes only application APIs. It never accesses the local database, external disclosure/market/model providers, or secrets directly.
- Result/request state distinguishes `empty`, `stale`, `partial`, and `error` where applicable, separately from capability availability (`available`, `conditional`, or `unavailable`). Neither axis is inferred from missing arrays or null metrics.

## Testing Decisions

- Acceptance suites are staged with the vertical slices that need them rather than built as one upfront framework: provenance/temporal invariants first; Watch Event lifecycle/replay and capability-state behavior next; Analysis golden/statistical cases only with the Analysis slice; provider conformance cases only with the market-data harness; and investigation evaluation only when a defensible independent target exists. Reuse the same highest application seam and compact fixtures across stages.
- Tests assert externally observable behavior at the highest stable seam. The primary acceptance suite feeds retained fixture evidence and recorded observations through the deterministic application boundary, then verifies API-visible Events, eligibility, Watch lifecycle history, capability states, Analysis manifests/results, and validated Findings. Tests do not assert private helper structure or a particular database schema.
- Existing backend API/application boundaries and read-only investigation tool boundary are preferred seams. New seams are introduced only for provider adapters, deterministic identity/temporal/lifecycle/Analysis services, and capability status where current V1 has no V2 contract.
- Golden provenance scenarios cover identical row occurrences, unchanged retrieval, changed artifacts, scoped amendments, candidate versus verified cross-source matches, malformed fields, negative latency, ticker reuse, ambiguous security identity, official/aggregator discrepancy, and parse-method recomputation.
- Temporal scenarios cover exact pre-open, during-session, after-close, exactly-at-open, weekend, holiday, early close, date-only, unknown timezone, delayed ingestion, old backfill, late correction, evidence narrowing, and later identity mapping. Each verifies both Public-information and System-observation As-Of behavior and forbids leakage.
- Event-study golden cases independently calculate anchor sessions, 1/5/20/60-session gross returns, cash distributions, splits, benchmark-relative log returns, direction alignment, missing bars, incompatible sessions, and unresolved terminal actions. Expected values do not come from the provider or production calculation path under test.
- Statistical tests use fixed synthetic cohorts to verify event weighting, member-cluster resampling, reproducible retained seeds, mandatory supported sensitivity estimates, directional-disagreement flagging, episode construction, four-week block resampling, thresholds for inferential availability, and null-result language. Property tests confirm invariance to row order and failure under forbidden future-evidence injection.
- Missingness scenarios verify that each missing field blocks only dependent uses, unavailable values never become zero, windows never silently shorten, multi-reason counts reconcile, and all denominators/sample dimensions remain visible.
- Filing-size scenarios verify distinct counting units, unresolved ranges, no size-based exclusion, indeterminate sensitivity classification, and no discretionary/passive label inference.
- Watch Event lifecycle scenarios cover the fifteen approved classes: admission/capabilities; transaction/public/system recency; unknown-age admission; active meaning; downtime; later evidence; 30-day policy; interval uncertainty; withdrawal/correction; timezone/DST/strict expiry; independent assessments; idempotency/recovery; reevaluation/current display; reinstatement; and continued admission criteria.
- Crash/replay tests verify atomic committed transitions, no duplication after retry, no invented downtime actions, separation of recorded history from recomputation, and preservation of prior outputs after method/evidence revision.
- Capability tests begin with market-dependent Analysis and Monitoring unavailable. No market result becomes available until a complete readiness fixture passes every gate. Partial provider evidence remains conditional or unavailable.
- Investigation contract tests verify read-only tools, bounded budgets, citation eligibility, future-evidence rejection, unexplained/incomplete outcomes, invalid-output rejection, free-text and structured no-advice enforcement, explicit application persistence, and operation without an LLM.
- Independent evaluation tests compare investigation selection to a frozen baseline and independently judged target set without using agent activity or narrative plausibility as success.
- API contract tests verify stable domain meanings, provenance fields, method/policy versions, availability reasons, and explicit empty/unavailable/conditional/stale/partial/error distinctions. Frontend tests verify those states are shown rather than collapsed.
- Graph tests verify navigation and relationship semantics, candidate/verified distinction, unavailable states, and that graph actions cannot alter evidence or calculate Analysis outputs. They do not freeze V1 layout constants or redesign presentation.
- Fixture-isolation tests prove demo/evaluation records cannot enter real queries or persistence. Secret scans verify credentials do not appear in frontend bundles, committed config, fixtures, logs, or API responses.
- Acceptance does not require a positive or statistically distinguishable result. A correctly produced null, negative, directionally disagreeing, small-sample, unavailable, or unexplained result passes when its evidence, methodology, coverage, and limitations are correct.

## Out of Scope

- Selecting, adopting, purchasing, or integrating a market-data provider; selecting a fallback provider; provider-specific behavior; or approving a revision-refresh policy.
- Activating market-dependent event-study results, market anomaly detection, return/volatility/volume thresholds, or market-triggered investigation before the market-data contract is satisfied.
- Historical Raw Consensus, Expected Consensus, Excess Consensus, their windows, baselines, proxies, backfills, polling, or production exposure. Unavailable never means zero.
- Adopting q, designing a Python/q split, or introducing numerical parity infrastructure without a separately approved measured need.
- UI or graph redesign, visual styling decisions, layout tuning, animation changes, or replacement of the existing frontend architecture.
- Implementation tickets, database schema selection, queue/transaction framework selection, scheduler implementation, migration execution, or provider SDK selection.
- New asset classes beyond purchases and sales of individual publicly traded equities; options, funds, bonds, commodities, cryptoassets, or inferred portfolio positions.
- Causal inference, member-performance ranking, alpha claims, trading simulation, execution, portfolio construction, or buy/sell/hold advice.
- Inferring discretion, passivity, adviser control, personal direction, conviction, or intent from filing size, transaction direction, or missing source statements.
- Minute-level or intraday market data, always-on infrastructure, paid core data/model dependencies, or a local-model/multi-agent/adversarial research system.
- Automatic additional source searches, relaxed readiness contracts, third Consensus evidence attempts, or unsupported coverage claims.

## Further Notes

- Source of truth for the completed decision map: [Signal V2 architecture and research methodology map](https://github.com/AviSharma01/signal-workspace/issues/1).
- Approved decision provenance remains in the linked resolution comments in that map. This specification incorporates those rules rather than duplicating their approval history.
- Contradiction audit: no genuine contradiction was found between this specification and an approved Wayfinder decision. Selecting SPY as the benchmark instrument and fixing return/window/statistical semantics are expressly delegated specification decisions; they do not select or certify a market-data provider. The specification preserves the unchanged market-data contract and keeps every dependent capability unavailable until it passes.
- The 15-literal-ticker split is included only as an outcome-blind legacy sensitivity allowed by the approved bulk-treatment decision. It is not the primary cohort rule, a universal cutoff, a resolved-security count, or a behavioral label.
- The 20-session primary horizon and 1/5/60 supporting horizons are Analysis outcomes only. They do not alter the separate 30-calendar-day Watch Event operational attention policy.
- Implementation simplicity guidance is binding on decomposition but does not change domain semantics: logical services do not require module/table proliferation; reproducible retained bootstrap seeds need no prescribed hash; capability availability and result state remain separate; non-market anomaly implementation waits for approved deterministic criteria; initial investigation budgeting uses only the minimum enforceable controls; and acceptance suites are staged with their vertical slices.
- Implementation handoff for `/to-tickets`: decompose vertical slices around (1) evidence preservation and identity/temporal eligibility, (2) Watch Event admission/lifecycle/replay independent of market data, (3) explicit capability-state APIs and UI handling, (4) market-data contract conformance harness with all dependent features still disabled, (5) deterministic event-study engine activated only by readiness, and (6) bounded investigation/validation. Preserve the highest-seam acceptance suite in every slice. Do not create provider-adoption, Consensus, q, or UI-redesign tickets from this specification.
