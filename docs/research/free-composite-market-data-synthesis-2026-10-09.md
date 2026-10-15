# Signal V2 free market data: research synthesis and free-first handoff

**2026-10-09; decision support, not provider approval or a specification change.**
This memo updates the prior free-composite synthesis with the completed
[ordinary-cash-dividend validation](free-ordinary-cash-dividend-validation-2026-10-09.md).
It changes no code, issue, capability, readiness state or approved V2 semantic.

## Current project decision — 2026-10-15

The accepted [free-first operating-mode ADR](../adr/0001-free-first-operating-mode.md)
selects **Strategy A: free-only operation with a useful disclosure-first
workspace**. No paid provider, purchase, subscription or paid-data trial is
authorized. Production market readiness under #31 remains unavailable, and
market-dependent Analysis/Monitoring stays gated under the unchanged V2 method.

The next product milestone is the bounded House disclosure workflow, using
application-owned, evidence-backed historical identity and explicit eligibility
limits. The independently validated calendar remains a future integration
candidate; OpenFIGI remains optional enrichment rather than historical authority.
kdb+/q stays deferred and optional. Existing provider-neutral boundaries preserve
a separately approved future paid route without introducing an adapter now.

The recommendation below to consider Strategy C was **historical decision
support dated 2026-10-09**, not the active project decision. It is preserved to
explain the trade-off. No further provider search, trial or methodology change
is authorized by this synthesis. The calendar, identity and dividend research
does not certify a complete free market-data stack.

## Historical research conclusion — 2026-10-09

**A contract-complete, free-only production market-data stack is not presently a
practical Signal strategy.** The evidence does not prove that no such stack can
ever exist. It does show that continued generic provider research has poor
expected value: a mandatory ordinary-cash-dividend component remains incomplete,
the near-complete structured histories observed cannot be retained and replayed
under their published terms without permission, and event-by-event reconstruction
does not look reasonable for a solo-project population.

The recommendation at that time was **a new project/specification decision about
whether Signal may eventually use a tightly bounded, low-cost paid market-data
component while preserving the full [#31 contract](https://github.com/AviSharma01/signal-workspace/issues/31)
and [approved V2 methodology](../specs/signal-v2.md)**. If paid data remains out
of scope, choose the free-only constraint explicitly and accept that
market-dependent production capabilities stay unavailable. Do not create a
data-available security subset or relax the methodology as an implementation
workaround.

## Evidence now established

The governing boundary remains [#26](https://github.com/AviSharma01/signal-workspace/issues/26),
V2 §§5–9 and the [provider-neutral conformance contract](../market-data-conformance.md):
five complete calendar years plus the current year, original regular-session
OHLCV, separate actions, historically scoped identity/listing joins, explicit
missingness, retained observed revisions, replay, workload evidence and rights.
Synthetic conformance or snapshot presence cannot activate production readiness.

The completed screens are the [Stooq experiment](stooq-technical-screen-2026-10-07.md),
[Twelve Data Basic screen](twelve-data-basic-screen-2026-10-08.md),
[corporate-action screen](free-corporate-action-component-screen-2026-10-08.md),
[NYSE public-MEF check](nyse-public-mef-screen-2026-10-09.md),
[historical-identity screen](historical-security-identity-screen-2026-10-09.md),
[bounded identity/workload experiment](historical-security-identity-feasibility-workload-2026-10-09.md),
[OpenFIGI META/METV experiment](openfigi-meta-metv-experiment-2026-10-09.md),
[calendar validation](exchange-session-calendar-validation-2026-10-09.md), and
the completed [dividend validation](free-ordinary-cash-dividend-validation-2026-10-09.md).

The dividend validation is decisive for strategy, although not a universal
impossibility proof:

- Positive events can often be reconstructed from original issuer/EDGAR terms
  plus authoritative exchange evidence. U.S. SPY for 2021–2025 and one NVIDIA
  event were fact-complete bounded examples.
- A no-dividend interval can occasionally be established when an attributable
  source explicitly states the negative, as Tesla did. An empty feed or missing
  filing remains **UNKNOWN**, not zero actions.
- Permitted primary sources do not supply complete, scalable ordinary-dividend
  discovery with event-specific ex-dates, corrections and explicit no-action
  coverage.
- The near-complete State Street and Nasdaq-hosted histories observed have
  retention/extraction restrictions incompatible with #31 unless permission is
  obtained. Free reading is not retained-input permission.
- Manual event-by-event reconstruction requires discovery, original-share-basis
  checks, ex-date/exception evidence, identity joins, rights review and revision
  handling. The six-case panel did not establish a reasonable population-scale
  solo workload.

## Component matrix

**PLAUSIBLE** means a validated or credible bounded component, not stack
readiness. **UNRESOLVED** means required semantics, coverage, rights or workload
remain unproved.

| Required component | Classification | Current conclusion |
|---|---|---|
| Exchange/session calendar | **PLAUSIBLE — validated** | Pinned `exchange_calendars==4.13.2` matched all 1,448 completed sessions through 2026-10-08, including holidays, early closes, ET/UTC, DST, year boundaries and the Carter closure. Retain the version/output and check later extraordinary closures authoritatively. This does not certify vendor bars. |
| Stable-ID enrichment | **PLAUSIBLE — validated for its bounded role** | OpenFIGI returned distinct META/METV composite and share-class FIGIs. Use only after dated evidence establishes the historical relationship; current metadata supplies no historical validity or listing interval. |
| Ordinary cash dividends | **UNRESOLVED — tested free route not practically defensible** | Individual positives and occasional explicit negatives are possible. No permitted, retainable, complete discovery/no-action/revision route was established, and manual population reconstruction is not a reasonable current solo plan. |
| Historical/raw prices | **UNRESOLVED** | Stooq supplied useful depth but defaults to adjusted data; its skip output is not certified original OHLCV and terminal coverage failed in the panel. Twelve documents `adjust=none` but the bounded demo did not validate required history or raw semantics. |
| Regular-session semantics and source rights | **UNRESOLVED** | Exact daily feed/volume scope, auctions/late trades, extended-hours exclusion, early-close/DST behavior, retention, derived display and termination rights are not cleared for a price route. |
| Splits and selected lifecycle/non-cash events | **PLAUSIBLE as evidence components** | Original SEC/issuer terms plus exchange dates can support bounded cases. Complete discovery, joins, currency/class semantics, correction history and terminal treatment remain unresolved; affected outcomes must fail closed. |
| Historical identity continuity | **PLAUSIBLE for the bounded cases; complete coverage UNRESOLVED** | The six-case identity/workload experiment supports distinct classes, listings and dated transitions, with retrospective human-work estimates. It does not establish population completeness or every interval. TWTR pre-open public availability remains UNKNOWN; EDGAR acceptance is not publication. Current FIGIs supply enrichment only. |
| Retained revisions and operational workload | **UNRESOLVED** | Application snapshots, hashes and offline replay are technically credible. Rights, real changed-version evidence, refresh scope and population-scale acquisition/review cost remain unproved. |

## Project-level strategies

| Strategy | Methodological integrity and missing-data bias | Usefulness and expected coverage | Engineering and solo maintenance | Reproducibility, V2 compatibility and portfolio value |
|---|---|---|---|---|
| **A. Keep the full contract and free-only constraint** | Highest integrity: no unsupported market result is produced, so missing data creates unavailability rather than a biased estimate. | Production market coverage remains zero until evidence improves. Disclosure ingestion, evidence inspection, eligibility/coverage reporting, Watch Event lifecycle, non-market Monitoring and bounded investigation remain useful. | Lowest new market-data complexity and burden; some ongoing source-readiness observation remains. | Fully compatible with the approved V2 methodology. Strong evidence-discipline and local-first portfolio value, but the central market-information hypothesis cannot be tested in production. |
| **B. Use a bounded, evidence-complete market subset** | Defensible only if the boundary is outcome-blind, source-independent, predeclared and complete. A subset chosen because free data exists introduces availability, issuer-size, survivorship, payout-policy or terminal-history bias. | Unknown and probably narrow/unstable. It may support an explicitly limited exploratory result, not a claim about the approved population. | High burden: enumerate the population first, prove complete coverage inside it, explain every exclusion and revalidate the boundary as identities/actions change. | V2 can represent event-level unavailable outcomes and exact scoped evidence. It does **not** authorize redefining the primary study around convenient securities. A deliberately narrower security population requires a new specification decision and would reduce research value unless independently justified. |
| **C. Keep the goals; permit a low-cost paid component later** | Best route to preserve the approved population, total-return method and missingness rules. Payment does not confer validity; #31 still applies unchanged. | Potentially broad 2021–current and terminal coverage, subject to independent validation. This is the only strategy likely to unlock the intended Analysis without selecting on data availability. | A provider adapter, rights review and conformance work remain, but a structured source should be substantially cheaper to maintain than manual multi-source reconstruction. | Architecturally aligned with the existing adapter/readiness boundary. A new decision is required because provider selection/purchase and paid core data were outside #26. If retained versions and derived use are allowed, auditability and portfolio value remain high. |
| **D. Change market scope or methodology** | Would have to relax or redesign at least one of: total-return semantics, original unadjusted inputs, separate actions, retained revisions, 2021–current history, the approved population, terminal handling or historical identity. Adjusted-price substitution, excluding dividend payers/terminal names or shortening windows can create material bias. | Nominal coverage could rise, but the result would answer a different question and may become incomparable across issuers or time. | Source integration might become simpler, but specification, test fixtures, interpretation and migration all become more complex. | Requires an explicit replacement specification and method version. Not recommended now: the tradeoff weakens the project's research and portfolio value more than the current evidence justifies. |

### What a paid component would have to solve

No product or price decision is made here. A future paid route would need to
close, alone or in a validated composite, these responsibilities:

1. Original unadjusted regular-session daily OHLCV for each resolved security
   and SPY, including field/feed/volume, currency/unit, session and finality
   semantics; complete 2021–current and delisted/terminal coverage; gaps,
   catch-up and changed-bar behavior.
2. A complete separately attributed ordinary-cash-dividend ledger with original
   per-share amount, currency, ex-date, type/share basis, historical-security
   join, corrections and explicit no-action coverage.
3. Complete split, non-cash and lifecycle/terminal discovery and terms sufficient
   either to calculate an approved result or mark only the affected window
   unavailable without inventing a terminal return.
4. Historically scoped security/listing/ticker continuity, including rename,
   reuse, class, transfer and delisting boundaries.
5. Rights to retain exact observed inputs and older observed revisions, replay
   locally, and display/store permitted derived Analysis after the relevant
   lifecycle or termination events.
6. Measured, reproducible backfill, daily acquisition/catch-up, revision refresh,
   joins and computation within a solo-project workload.

Free components remain useful: the validated pinned calendar; OpenFIGI stable-ID
enrichment; dated SEC/issuer/exchange evidence for identity/action reconciliation;
public exchange lifecycle notices where rights apply; and Signal's own snapshots,
hashes, provenance, conformance, missingness and replay machinery. A paid source
would supply missing evidence, not replace independent expectations or the
application-owned audit trail.

## Historical answers and recommendation — 2026-10-09

1. **Is continued free-only research rational?** Not as an open-ended production-
   stack search. The remaining work is not another provider-name search; it is a
   rights/completeness/workload problem already demonstrated by the dividend
   component. Passive reconsideration is rational if materially new primary
   evidence appears.
2. **Is there a defensible bounded-market subset under the existing spec?** The
   spec already permits individual outcomes to be unavailable and requires full
   flow/missingness reporting. That does not make a source-selected subset a new
   primary population. No source-independent, evidence-complete subset is now
   demonstrated. A deliberately narrower security universe would materially
   change the study and requires a new specification decision; shorter coverage
   is only exploratory under #26.
3. **Can Signal remain useful without market readiness?** Yes. Disclosure-only
   evidence, identity/temporal eligibility, Watch Event lifecycle, capability
   transparency, coverage/missingness research, navigation and non-market bounded
   investigations remain real product value. Market outcomes, anomaly detection,
   market-dependent Monitoring and market-triggered investigation remain
   unavailable rather than silently degraded.
4. **Which free components are worth implementing regardless?** The pinned
   validated calendar and its retained closure checks; optional OpenFIGI
   enrichment behind dated identity evidence; reusable SEC/issuer/exchange
   evidence capture for identity/action reconciliation; and application-owned
   provenance/snapshot/replay behavior. None should be labeled a complete price,
   action or identity source.
5. **Single best next milestone:** decide and record whether a capped low-cost
   paid market-data component is allowed while leaving #31 and V2 methodology
   unchanged. If allowed, the next research can be a small requirements-led
   product comparison against the six responsibilities above. If rejected,
   explicitly adopt Strategy A.
6. **Explicit free-research stopping condition:** stop proactive free-only source
   research once one mandatory component has no permitted complete discovery,
   retention/replay and reasonable measured solo-workload path after bounded
   validation. The ordinary-cash-dividend result meets that condition now.
   Reopen only for new primary evidence that names a complete retainable route;
   a new API example or another individually reconstructable event is insufficient.
7. **Implement, research once more, or decide?** Make the new specification/project
   decision now. Do not begin a production adapter, redefine a subset or relax
   methodology. Calendar and identity-enrichment implementation are low-regret
   later work, but they do not change the strategic blocker and should not be
   mistaken for market readiness.

**Historical recommendation: Strategy C, contingent on explicit approval; Strategy A is
the honest fallback. Do not pursue B as a data-availability workaround, and do
not pursue D without a separately justified replacement methodology.**

The 2026-10-15 ADR selected Strategy A. The historical request for a paid-data
decision is resolved by that free-only choice; it is not outstanding work.
