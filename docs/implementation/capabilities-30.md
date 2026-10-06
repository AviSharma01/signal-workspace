# Capability and result-state implementation (#30)

These descriptive notes record the #30 implementation on top of completed #29
at `e15f9194d362f81df18bdad11f0b67de30fcb5ae`. Authority remains approved
[#26](https://github.com/AviSharma01/signal-workspace/issues/26),
[#30](https://github.com/AviSharma01/signal-workspace/issues/30), the closed
Wayfinder decisions, and repository AGENTS instructions. These notes approve no
new provider, method, threshold, Consensus definition, investigation runtime, or
active-only action.

## Contract and initial capability matrix

`signal-capabilities@1` defines one API shape for capability availability:
`id`, `name`, `availability`, stable `reasonCodes`, human-readable `detail`,
`evaluatedAt`, `governingVersion`, and structured `unmetPrerequisites`.
Availability is exactly `available`, `conditional`, or `unavailable`.

Request/result status is a separate object with `state`, `detail`, and
`evaluatedAt`. The implemented states are `empty`, `stale`, `partial`, `error`,
and `successful`. Neither contract derives the other from null values, empty
arrays, HTTP success, or missing records.

`GET /api/capabilities` exposes the current matrix. Retained disclosure evidence,
Event derivation, and Watch lifecycle are available. Disclosure discovery and
disclosure-only coverage derive from chamber gates: conditional chamber evidence
stays conditional and cannot activate them, while the current House and Senate
unavailable gate results from #27 keep both dependent capabilities unavailable. The
market event study, market outcomes, market Monitoring checks, market anomaly
detection, Raw/Expected/Excess Consensus, V2 investigation runtime,
market-triggered investigation, and investigation-selection evaluation are
unavailable with stable reasons and prerequisites.

Market-dependent capabilities share the unchanged minimum market-data contract.
Anomaly detection additionally requires separately approved deterministic
thresholds. The V2 investigation runtime remains the #34 boundary. Historical
Consensus remains deferred after unsupported evidence attempts and exposes no
numeric value.

## Existing V2 API integration

Disclosure evidence, Event queries, and Watch Event list/detail/admission reads
now carry capability and result objects without removing their established #27,
#28, or #29 fields. Disclosure evidence reports empty, stale, partial, failed, or
successful processing separately from evidence-retention availability. Event
queries distinguish an available derivation capability from a valid empty
result. Watch reads distinguish lifecycle capability, result freshness, market
check outcome, evidence standing, admission criteria, recency, active
eligibility, current evaluation, last persisted assessment, difference flags,
and recorded history.

The execution-time boundary is unchanged. Displayed capability or active
eligibility is not authorization. `WatchApplication.authorize_active_action`
still reevaluates under the actual clock and current evidence immediately before
active-only application work; its response remains valid only for that immediate
application action.

## V1 containment and frontend

The V1 price endpoint retains its route but excludes seeded/local V1 rows and
returns an unavailable production-market capability plus an explicit empty
result. The legacy findings endpoint similarly excludes V1 findings from the V2
investigation surface. `POST /api/scan/run` now rejects execution with HTTP 409,
an unavailable legacy-scan capability, and an error request state. Underlying V1
modules and stored records are not deleted.

News/discussion graph records are labeled `legacy_v1_context` and explicitly are
not V2 Events, candidate or verified occurrence relationships, anomalies, or
Findings. Graph edges carry a declared legacy context relationship type and
evidence basis. Candidate and verified relationship meanings in the Event spine
are unchanged and remain distinct.

The existing graph, disclosure evidence/Monitoring page, company detail chart,
company side panel, Watch panel, and investigation panel render capability and
result states with the existing muted visual language. Unsupported market and
scan controls are disabled; unavailable V1 price and Finding records are not
rendered as V2 results. No database, provider response, credential, or secret is
accessed from the browser.

## Boundary after #30

#31 may validate and adopt a market-data provider only by satisfying the
unchanged minimum contract. Until then, it must not change the initial
unavailable market outcomes, market Analysis, market Monitoring, anomaly, or
market-trigger states. If #31 succeeds, it can replace capability reasons only
through retained conformance evidence and normalized application APIs; it cannot
reuse V1 price rows as proof.

#34 may implement the bounded V2 investigation runtime, validated Findings, and
selection evaluation against an independent target/baseline. It must consume an
explicit capability snapshot and declared As-Of boundary, keep evidence tools
read-only, use application-owned persistence, preserve structural no-advice, and
continue to accept unavailable, incomplete, unexplained, or budget-exhausted
outcomes. #30 does not authorize the legacy V1 scan or add any active-only action.
