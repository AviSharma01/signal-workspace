# Event derivation implementation (#28)

Descriptive implementation notes for the uncommitted #28 changes based on
`72af9051681e7494ee1da241a673c14895bf11cd` (completed #27). Authority remains
[approved #26](https://github.com/AviSharma01/signal-workspace/issues/26),
[#28](https://github.com/AviSharma01/signal-workspace/issues/28), the closed
Wayfinder resolutions, and repository instructions. This document introduces no
methodology or source-readiness decision.

## Evidence handoff and application boundary

`DisclosureApplication.ingest_house_filing` retains an official artifact/content
version and retrieval observation before interpretation. `_process_house_ptr`
retains its extraction, independently identifies rows by version/source position,
and appends normalization linked to its extraction. `query_evidence` exposes the
artifact/version, extraction/method, row occurrence, original fields, source
filing, normalization and actual retrieval observations. Index rows never become
transaction occurrences. Supporting payloads retain separate authority and
provenance. No #27 evidence table is rewritten by Event derivation.

`EventApplication` reads that handoff. It accepts explicit, cited application
verification/interpretation commands and computes read views. There is no
value-based matching algorithm, inferred member/security identity, calendar
weekday fallback, provider adoption, model-callable mutation tool or automatic
promotion of supporting rows.

The additive schema stores only append-only `event_evidence_assertions` and
immutable `event_recorded_views`. Ordinary reads do not persist Events or source
changes. An Event's occurrence identity and its separately versioned view are
distinct: recorded view ID, method version, computation time, perspective,
As-Of boundary and input manifest identify the interpretation.

## Commands and reads

- `GET /api/events?perspective=public_information|system_observation&asOf=<ms>`:
  deterministic historical recomputation, with disclosure eligibility/coverage.
- `POST /api/events/evidence-assertions`: application-owned cited publication,
  relationship, identity, interpretation, scoped correction, calendar or context
  assertion. Records actual observation time; never accepts a client-supplied
  observation time or fixture population.
- `POST /api/events/views`: retain a historical recomputation or explicitly
  labeled corrected-retrospective view. The latter requires `originalAsOf` and
  a strictly later `asOf`.
- `GET /api/events/views/{id}`: return the actual immutable output recorded at
  `computedAt`, without claiming it existed at the selected historical As-Of.
- `GET /api/events/views/{id}/reproduction`: rerun the recorded method over pinned
  retained inputs and verify exact output equality; label the reproduction and
  its actual execution time separately.

Record keys are camel case at the router boundary. Original field keys, extracted
representations and reason-count keys are preserved. The application boundary
and physically isolated SQLite fixtures provide the acceptance seam.

Assertions are explicit evidence assessments, not proof inferred from arbitrary
name/ticker equality. Callers must supply verified source statements, historical
validity, citation locators and a recorded basis. Citations must reference
successfully retrieved versions in the same population. Official Event field
interpretations/corrections require official evidence. Verified correspondence
must cite both source representations. Distinct same-version rows cannot be
merged, including through transitive or conflicting historical relationships.
Rejection/resolution is appended and applied under its applicable boundary.

Publication evidence retains source text and precision. Exact instants require
an explicit offset. Date-only evidence retains a source-local interval, including
23/25-hour DST days; its end is a conservative eligibility boundary, never an
invented publication instant. Unknown zones and filing dates do not establish
publication. Retrieval availability is explicitly an upper bound, not publication.
Each factual input also requires supported availability of its cited versions.

Calendar assertions require retained citations, an exchange timezone, certified
complete regular-session coverage and explicit session opens/closes. The next
open must be strictly after availability, including exactly-at-open publication.
No production exchange calendar is seeded or certified by these fixtures.
Unavailable or conflicting calendar support yields an unavailable anchor.

## Historical state and later evidence

Original `publication`, `intrinsicBoundary`, `intrinsicState` and `anchor` use
evidence supported at the original publication boundary. Identity validity is
scoped to the reported transaction date, or supported source-local publication
date when transaction date is absent. Pre-session context must satisfy both the
requested perspective and the strict-before-open cutoff. Later corrections,
identity mappings, publication proofs and calendar revisions cannot overwrite
the frozen original state or anchor. Relationship provenance at the requested
As-Of is distinct from the original counting assessment.

System-observation views describe actual locally observed evidence and current
interpretation through their selected cutoff. Improved processing of eligible
original artifacts is allowed in separately labeled historical recomputations
under either perspective. It does not establish that the historical system
produced the new result. Recorded output reproduction pins the prior source,
assertion, extraction, normalization and observation IDs.

`currentPublication` is available only in System-observation or
corrected-retrospective views. It exposes later supported publication intervals,
public proof availability and actual local proof observation separately.
`retrospectiveAnchor` is explicitly derived from later eligible interpretation;
it never replaces `anchor`. A previously unknown publication can become
interpretable here without becoming eligible for an earlier primary cohort.

Eligibility reasons are stable and non-exclusive. Amount and transaction-date
missingness block their dependent features, rather than a defensible disclosure
study. Coverage includes denominators, reasons, chamber, year, source role,
direction and per-artifact-version filing completeness/counting units. Incomplete
counts are minima; absent literal-ticker extraction is indeterminate, not zero.
No filing size exclusion or behavioral label is applied.

## #28 acceptance mapping

| Acceptance criterion | Focused application/API scenarios |
| --- | --- |
| Occurrence-level Events; verified sharing only | Identical rows; candidate/verified/rejected relationships; transitive collisions; different public/system relationship ordering; row-order invariance |
| Aggregator-only discovery candidates | Separate supporting authority; primary/Watch prerequisite exclusion; API population/citation isolation |
| Date evidence remains an interval | Date-only conservative cutoff; unknown zones; filing date; DST-length days; later publication narrowing |
| Exact-at-open uses next open | Pre-open, exactly-at-open, during-session and after-close literal expected opens |
| Calendar/timezone rules | Weekend, July 4 holiday, July 3 early close, explicit exchange zones and incomplete-calendar rejection |
| No later factual evidence leakage | Delayed ingestion; later mappings; scoped amendments; future citations; late observations; frozen listing/calendar anchor |
| Dependent-use missingness and reasons | Missing amount/date; explicit null correction; member/security ambiguity; non-exclusive counts and filing completeness |
| Preserve outputs and label later views | Immutable API output; pinned deterministic reproduction; improved parser recomputation; separately labeled corrected publication/state/anchor |

## Readiness, limitations and #29 handoff

These are disclosure-only Event assessments. House/Senate readiness remains
unavailable under #27's unmet validation gates; uneven coverage is never a
complete panel. Market outcomes remain unavailable. This slice performs no
Watch admission/lifecycle, outcome calculations, statistical cohorts, anomaly
detection, Consensus, q work, behavioral inference or UI redesign.

The implementation consumes curated cited identity/publication/relationship
assessments and retained validated calendar snapshots. It does not create a
production identity reference dataset, discover publication history, validate a
calendar provider, or certify chamber coverage. #27's unsupported/scanned PDF
and unresolved-continuation limits remain explicit.

For [#29](https://github.com/AviSharma01/signal-workspace/issues/29), retain a
System-observation Event view at the actual evaluation time. Consume its Event
and occurrence IDs, official provenance, identity/standing assessments,
`watchAdmissionPrerequisites`, `firstObservedAt`,
`officialEvidenceFirstObservedAt`, original and current publication support,
actual assertion-observation times, method version and input manifest. Official
retrieval time is not an invented verification or admission time. #29 owns actual
verification/admission persistence, the original-publication 30-calendar-date
America/New_York clock, recency/expiry uncertainty, active eligibility, committed
transitions and recovery. Unknown publication can permit prerequisites while
withholding active-only uses; market data is never an admission prerequisite.
