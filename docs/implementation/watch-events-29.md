# Watch Event lifecycle implementation (#29)

Descriptive notes for the uncommitted #29 changes based on completed #28 at
`d8d9c165a93190e66e5d10ffa6b61b030ccad603`. Authority remains approved
[#26](https://github.com/AviSharma01/signal-workspace/issues/26),
[#29](https://github.com/AviSharma01/signal-workspace/issues/29), the closed
[#23 resolution](https://github.com/AviSharma01/signal-workspace/issues/23#issuecomment-5744594273),
and repository AGENTS instructions. These notes approve no new policy.

## Production handoff and admission

The application evaluates retained evidence through #28's `EventApplication` at
the actual clock, using System-observation As-Of. Its view provides an Event,
official occurrence/artifact provenance, publication claims, current standing,
member/security identities, `watchAdmissionPrerequisites`, actual retrieval and
assertion observations, method version and input manifest. A committed Watch
assessment retains that source view and its manifest. No caller may supply a
verification, admission, evaluation or observation timestamp to the API.

`POST /api/watch-events/admissions` is the explicit application-owned verification
and admission command. It checks the current recorded evidence, then commits the
Watch Event and first lifecycle assessment together. Verification and admission
have separate fields; this command performs both at the same actual time. It does
not infer verification from an earlier official retrieval. Discovery preserves
the earliest eligible filing discovery/occurrence observation. Official-evidence
observation remains a separate field. It does not depend on prices, an exchange
calendar, market readiness, anomaly detection or a model. Unknown publication
age can admit while withholding active uses. Admission after expiry is supported.

Admission is explicit, rather than automatic promotion by ingestion. #28's
curated cited identity/interpretation commands remain the verification input;
this slice adds no automated identity or publication-history dataset.

## Lifecycle, evidence and persistence

`WatchApplication` owns two additive SQLite tables: immutable admissions and
append-only committed assessment history. It uses the existing connection
factory. Lifecycle commands take a SQLite write transaction before reading the
evidence and actual clock; nested Event/disclosure reads share that transaction.
Assessment and transition persistence is atomic. No queue or persistence
framework is added. A failed transaction leaves prior history intact.

Evidence standing, continued admission criteria, recency, expiry support,
active eligibility and all blocking reasons are separate fields. Supported
out-of-scope corrections fail criteria without becoming withdrawals. Withdrawal
and expiry can overlap. Reinstatement requires an explicit `standingResolution`
(`reinstatement` or `withdrawal_misattributed`) on a supported official correction,
with a cited official artifact version first observed after the withdrawal.
Re-fetching an unchanged old artifact, or merely setting standing to supported,
cannot reverse withdrawal.

`watch-lifecycle@1` applies the approved 30 calendar dates in America/New_York.
Exact publication retains the local clock across the date addition. Ambiguous
expiry uses the earlier instant; nonexistent expiry advances to the first valid
instant. Eligibility is strictly before expiry. Date-only source evidence remains
an interval, eligible after its supported source-local day ends. Extrema over
every supported publication instant include New York fold/gap discontinuities.
The supported expiry range has an earliest and latest bound at millisecond
storage precision; it is never an invented exact expiry. At the earliest bound,
mixed expiry support withholds active eligibility; at the latest bound all
supported instants have expired.

Admission retains its official artifact version and occurrence as immutable
identity/history references, not an irrevocable publication-evidence selection.
Current clock selection considers eligible official original representations in
#28's verified Event membership. A shared #28 original-representation helper
excludes amendments and their verified same-occurrence copies from both Event
base selection and Watch clock evidence. Later conclusive amendment attribution
can also invalidate the admission representation as a clock source without
deleting the Watch or changing its recorded admission.

Compatible evidence is selected per artifact under #28's publication contract.
Across verified original representations, first availability is the minimum of
their supported publication times, not an intersection of different copies'
publication dates. Its supported interval retains the earliest lower bound and
tightest upper bound, including exact upper support at millisecond precision.
Thus later verified earlier availability can shorten expiry, while a later copy
cannot restart the original clock. Date-level uncertainty is not converted into
an invented exact instant. Conflicting claims within an artifact withhold
eligibility. Discovery, downtime, correction and reinstatement are not clocks.
Prior unknown/uncertain/active assessments stay recorded at their actual times.

Unchanged semantic assessments append nothing, including repeated identical
evidence assertions, retrievals, admissions and recovery. Relevant changed
standing, criteria, recency, expiry support or reasons persist even when activity
remains false. Source evidence commits before lifecycle reevaluation; a crash in
between is repaired from committed evidence at actual recovery time.

## Reevaluation and APIs

Reevaluation runs on admission, committed evidence assertions and relevant
disclosure extraction/normalization changes, startup/recovery, the known next
expiry boundary and immediately before an active-only application action.
The existing APScheduler owns one replaceable expiry date job, a startup recovery
job and a one-minute local recovery check for an interrupted assessment or job.
Nothing runs while the local application is stopped. Misfires and downtime
record actual execution/persistence time; they never manufacture past transitions.

- `GET /api/watch-events`: admitted Watches with current evaluation, last persisted
  assessment, stale/difference flags, current Event provenance and recorded history.
- `GET /api/watch-events/{id}`: the same detail for one Watch.
- `POST /api/watch-events/{id}/active-eligibility`: current reevaluation plus
  immediate-use lifecycle authorization, persisting any meaningful change.
- `GET /api/watch-events/{id}/assessments/{assessmentId}`: actual immutable
  recorded history, accessible independently of current method availability.
- The assessment's `/reproduction` endpoint: reruns the recorded Event inputs
  and policy versions, verifies source/assessment equality and labels the actual
  reproduction time. Unsupported versions are rejected.
- `/recomputation`: a read-only historical recomputation using evidence eligible
  at the original System-observation boundary and current supported processing.
- `/corrected-retrospective?asOf=<later-ms>`: an explicitly later evidence view
  evaluating the original historical time; it cannot rewrite history or assert
  that later publication was already available at that time.

Only the real population is exposed by HTTP. Source/raw maps remain unchanged;
record keys are normalized at the router. Read APIs never persist assessments.
The existing evidence inspection page includes a Watch detail panel and refreshes
current evaluations every 30 seconds. Both the Monitoring graph and company
detail navigation link there. It displays evaluated time, earlier persisted
state, lifecycle reasons/history, publication precision and evidence provenance.

## Acceptance coverage

| #29 acceptance criterion | Application/API scenarios |
| --- | --- |
| Market-independent admission | Eligible official Event with no market rows; unknown publication admission; no calendar requirement |
| Exact/interval 30-date New York policy | Exact expiry; source-local date intervals; ambiguous and nonexistent expiry; interval ending at a repeated New York hour |
| Strict expiry and conservative uncertainty | Millisecond before/exact expiry; straddling interval; latest supported bound; later compatible narrowing |
| No publication-clock resets | Downtime/restart; delayed catch-up; correction/reinstatement; verified amendments and copies; earlier/later verified original representations; conflicting later publication |
| Old verified admission | First admission well after original expiry remains inactive |
| Distinct standing/criteria/history | Withdrawal, unresolved standing, supported out-of-scope correction, overlapping withdrawal/expiry, explicit reinstatement |
| Retry/crash idempotency | Repeated admission/evidence/recovery; failed attempt; actual subprocess crash after insert before commit |
| Committed history only | SQLite fault injection preserves prior history; rolled-back admission exposes no Watch; recorded reads/reproduction unchanged |
| Actual recovery times | Overdue expiry and failed transition recover at the later actual execution time, with no downtime entries |

Additional scenarios cover current versus stored assessment, pre-action
reevaluation, fixture isolation, assessment/Watch path ownership, four distinct
replay perspectives and rejection of unsupported reproduction versions.
Relationship-split regressions keep the original admitted occurrence queryable;
merging two already-admitted occurrences preserves both histories while
withholding duplicate active authorization and refusing a third admission.
Required-identity conflicts produce unresolved standing rather than a conclusive
out-of-scope failure. Reinstatement remains explicit after intervening unresolved
standing.

## Verification of this change

The focused application/API/scheduler suite passes all 46 tests. The full backend
suite passes all 127 tests, including source/bundle secret checks. Python
compilation, both TypeScript projects, ESLint, production build, and
`git diff --check` pass. The build retains the existing large-chunk warning.
Build/type checks used the already-installed Node 22.22.2 runtime; the default
Node 20.16 runtime is incompatible with the installed Vite/native build tooling.
New UI files pass Prettier. The existing `DetailPage.tsx` has baseline formatting
differences; the new navigation button is formatted without rewriting unrelated
lines.
The Monitoring panel was checked in the browser against a physically isolated
temporary fixture database, including current-expired versus persisted-active,
unknown publication age, and interval-uncertain states.

Scoped Standards and Spec re-reviews report no remaining findings. Review fixes
and regression tests address relationship splits/merges, identity uncertainty,
explicit reinstatement history and reuse of the pre-action evaluation. The final
publication-clock audit adds regressions for earlier verified originals, later
copies, amendment copies and later amendment attribution, interval upper bounds,
unchanged historical reproduction, historical evidence exclusion, corrected
retrospective results and actual-time recovery after a failed transition.
The July 9 admission / later July 3 same-occurrence evidence / August 3 action
reproduction now derives August 2 at 09:00 EDT expiry and denies authorization.
No Git commands were run for this corrective slice; targeted source whitespace
checks were used instead of repeating `git diff --check`.

## #29 → #30 handoff and limitations

#30 consumes `watchEvent`, `currentEvaluation`, `lastPersistedAssessment`, stale
and difference flags, and `lifecycleHistory`. `activeEligibility` is only the
lifecycle prerequisite; it conveys no capability readiness or check outcome.
Any future active-only application action must call `authorize_active_action`
at its execution boundary using the actual clock, and independently satisfy its
capability contract. A displayed/read assessment or a prior HTTP eligibility
response is not a durable authorization token.

The original #27/#28 source/readiness limitations remain: curated cited
interpretations, no production identity/publication/calendar dataset, unsupported
PDF cases and unvalidated chamber coverage. This slice supports retained
publication exact/date intervals; it adds no source adapter claiming precision
beyond that evidence. Market work, anomalies, automatic investigation, Consensus,
q and the cross-product capability contract remain outside #29. The existing V1
market/scan surfaces are left for #30's explicit capability treatment.
