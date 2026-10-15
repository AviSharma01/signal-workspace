# Twelve Data Basic/free bounded screen

Observation date: **2026-10-08**. Research/testing only; no provider adoption,
integration, production-readiness change, or relaxation of
[#31](https://github.com/AviSharma01/signal-workspace/issues/31).

**Twelve Data Basic cannot satisfy #31 alone.** Separate splits/dividends are
paid. It remains a **conditional price-component research lead**, with no role
yet independently cleared for Signal. Storage/display rights, raw daily volume,
historical identity, terminal coverage and revision semantics remain unresolved.
An eight-request public-demo probe does not establish authenticated Basic access.

Publication review, **2026-10-15**: this independently authored report is proposed
separately from the locally held `experiments/twelve-data-2026-10-08/` bundle.
That original bundle, including raw responses, copied provider documentation,
headers, scripts, manifests and verification outputs, remains unchanged and
excluded because retention/redistribution rights are unresolved. This report
contains a factual methods/limitations assessment and primary-source links,
not copied documentation or an OHLCV dataset. The committed repository cannot
replay the probe without those excluded inputs; hash checks performed locally
are not semantic conformance or permission to publish them.

First inspected: [#31](https://github.com/AviSharma01/signal-workspace/issues/31),
[provider-neutral contract](../market-data-conformance.md),
[#26](https://github.com/AviSharma01/signal-workspace/issues/26) market requirements,
[prior provider screen](free-market-data-provider-screen-2026-10-07.md), and
[tested Stooq screen](stooq-technical-screen-2026-10-07.md). Required coverage is
2021–2025 and completed 2026 sessions through **2026-10-07**: October 8 was still
open at retrieval. Neither full coverage nor the latest session was downloaded.

Success criteria: primary-source entitlement/semantic evidence, every exact
contract gate classified, bounded isolated responses/hashes, and a component
assessment. Sequence: contract → legal/free access → endpoint definitions →
small demo probe → offline verification. No Git operations, issue edits,
application imports, integration or normal data/database writes were performed.
This is a screen, not a conformance-harness report or an adoption decision.

## Rights and free-tier entitlement

**Documented fact:** Individual pricing covers personal/internal/noncommercial
use. Basic is $0, eight API credits/minute, 800/day, with internal non-display
usage; internal display is paid Grow. Solo/private use fits the category, but
raw-data display is outside advertised Basic entitlement.
[Pricing](https://twelvedata.com/pricing).

**Documented fact:** terms updated January 1, 2026 allow internal storage subject
to tier/documentation timeframes and third-party limits (§§2.2, 2.3(g), 16.1).
Compliant, non-reconstructable Derived Data remains customer-owned (§6.2).
Termination requires deleting Data; §16.2 specifies 30 days and a compliance
exception. Free commercial use, unauthorized redistribution and competing
products/composites are restricted (§2.3); financial derivative products require
permission. Source-code publication alone is not shown prohibited.
[Terms](https://twelvedata.com/terms).

**UNKNOWN:** Basic persistent-storage duration, raw-version retention, applicable
third-party limits and derived Analysis display. Data and Derived Data differ;
universal derived-output deletion cannot be inferred. No blanket Basic storage
ban was found; termination deletion prevents continuing raw-input replay then.
This does not silently add perpetual post-termination rights to #31.

**Inference:** a composite cannot repair incompatible component rights; private
use does not waive storage limits. **Empirical testing cannot settle licensing.**

Public reports/data displays require attribution; private analytics are exempt.
Attribution grants no missing entitlement.
[Attribution guidance](https://support.twelvedata.com/en/articles/12647398-attribution-guidelines-for-using-twelve-data).

## Historical prices and market semantics

**Documented fact:** daily history is advertised from first trading date for most
symbols, with `/earliest_timestamp` discovery and up to 5,000 rows per response.
Date-range/output-size interactions need checking; advertised depth does not
prove complete 2021–2026 sessions or delisted coverage.
[History guide](https://support.twelvedata.com/en/articles/5656039-how-to-get-historical-prices).

**Documented fact:** U.S. historical/EOD data starts at Basic, becomes available
after midnight ET on the next trading day, and is advertised as full-market
volume. The default real-time feed represents roughly 5% of trading volume;
OTC requires separate licensing. These are different feeds, and overnight EOD
availability is not vendor finality or guaranteed freshness.
[U.S. equities guide](https://support.twelvedata.com/en/articles/9935903-us-equities-market-data).

**Documented fact:** `/time_series` costs one credit/symbol, defaults to
`adjust=splits`, and supports `none`, `splits`, `dividends`, `all`. Daily dates
use exchange-local time; the timezone parameter only applies intraday.
Metadata contains currency, exchange, MIC, timezone and instrument type.
`prepost=false` is the default, but the documented extended-hours switch applies
to selected intraday intervals, not a certified daily OHLCV cutoff.
[Time-series definition](https://twelvedata.com/docs/llms/market-data/time-series.md).
The older [adjustment FAQ](https://support.twelvedata.com/en/articles/5179064-are-the-prices-adjusted)
describes daily prices as split-adjusted without explaining the override; this
is not sufficient evidence that the current `none` option fails.

**Inference / empirical testing required:** explicit `adjust=none` makes original
prices more plausible than Stooq's inverse-adjustment skips. The NVDA split test
did not return bars, so genuinely original OHLCV, volume/share basis, regular-only
volume, auction/late-trade treatment, holiday/early-close cutoffs, DST and exact
SPY/security alignment remain **UNKNOWN**. Full-market volume does not mean
regular-session-only volume. No adjusted series was used to reconstruct raw bars.

## Actions, identity and lifecycle

**Documented fact / free-tier FAIL:** `/splits` and `/dividends` each cost 20
credits/symbol and require Grow/Venture or above. Splits expose date, description,
ratio and from/to factors; dividends expose ex-date and amount, with adjustment
defaulting to true. They are separate action records, but **not Basic components**.
Original dividend amounts with `adjust=false`, precise split-date meaning,
ratio orientation and action completeness would still need validation on an
entitled plan. No paid endpoint or paid trial was tested.
[Splits](https://twelvedata.com/docs/llms/fundamentals/splits.md),
[dividends](https://twelvedata.com/docs/llms/fundamentals/dividends.md).
The official [April 2026 update](https://twelvedata.com/news/april-2026-updates)
specifically corrected dividend documentation from payment date to ex-date.
General EOD marketing mentioning corporate actions does not override endpoint
entitlements or provide an original action ledger. Adjusted prices cannot replace it.

**Documented fact:** `/stocks` is a daily-updated catalog with exchange/MIC,
currency/type, `include_delisted` and `show_plan`. FIGI-filtered access is
Ultra/Enterprise; ISIN/CUSIP access needs add-ons. Its schema provides no dated
symbol/listing validity intervals or historical knowledge vintages.
[Stocks catalog](https://twelvedata.com/docs/llms/asset-catalogs/stocks-list.md).

**UNKNOWN:** FB→META resolution, ticker reuse separation, dated listing changes,
delisting dates/reasons, original terminal terms and historical delisted bars.
`include_delisted` is a discovery lead, not proof of complete terminal history or
a historical security master. The FB/META/TWTR demo rejections establish none of
those facts. A CIK identifies a filer, not an interchangeable security/listing.

**Documented fact:** dated `/exchange_schedule` requires Ultra/Enterprise and
100 credits/request; Basic cannot supply that endpoint as a calendar component.
Static exchange metadata cannot certify historical holidays/early closes.
[Exchange schedule](https://twelvedata.com/docs/llms/markets/exchange-schedule.md).
An independently validated free calendar could supply this responsibility in a
composite, without proving Twelve Data bars follow that calendar.

## Operations and revisions

**Documented fact:** quotas are credits, not an unconditional 800 HTTP calls;
batching still charges per symbol. Basic's eight/minute and 800/day permit small
panels, but do not establish a complete free workload budget.
[Pricing/credit examples](https://twelvedata.com/pricing).

**Inference:** roughly 1,450 daily rows/name for 2021–evaluation fit under 5,000,
so one price request/name might backfill that range. For N names, a single-request
backfill or daily catch-up needs at least N credits, N/8 quota minutes and
ceil(N/800) quota days, excluding other queries/retries/revisions. More than 800
names cannot all be individually refreshed daily under that assumption. This is
quota arithmetic, not measured Signal-universe feasibility. Catch-up date ranges
are plausible; no operational catch-up or historical refresh policy was approved.

**Documented fact:** EOD guidance distinguishes preliminary prices from prices
confirmed after exchange reconciliation. Its example and time-series schema
expose no per-bar confirmation flag or version ID.
[EOD confirmation guide](https://support.twelvedata.com/en/articles/12682324-end-of-day-eod-pricing-market-data).
`/last_change/{endpoint}` tracks fundamentals/actions; its documented endpoint
enumeration excludes time-series price bars.
[Last-change definition](https://twelvedata.com/docs/llms/fundamentals/last-changes.md).

**UNKNOWN:** correction publication timing, old-version access, price revision
enumeration, field-level finality and source availability vintages. Retained raw
responses plus hashes could detect observed byte changes if rights permit; they
cannot reconstruct what the vendor knew in 2021. A local observation time never
becomes a historical public-availability timestamp.

## Bounded empirical result

No local Twelve Data credential was found; no account was created. The documented
public demo key was used, distinct from authenticated Basic entitlement.
[Authentication/demo documentation](https://twelvedata.com/docs/llms/introduction.md).
Eight `/time_series` requests, at most ten rows each, ran between 16:29:12 and
16:30:11 UTC on October 8. An earlier Python TLS attempt failed certificate-chain
verification before receiving HTTP responses; it is retained separately. Curl
then used its working certificate store, with verification enabled. No universe
backfill, action request, intraday fetch or application write occurred.

| Case | Exact observed result | What it establishes |
| --- | --- | --- |
| AAPL Jan 4–8, 2021, `adjust=none` | HTTP 200; four daily rows Jan 4–7, USD, America/New_York, NASDAQ/XNGS | A small dated response with metadata; not full history/raw certification |
| AAPL repeated request | HTTP 200; identical 679-byte body, different HTTP headers | One unchanged body retrieval; no changed-revision case |
| SPY Jan 2021 | HTTP/API 401 demo restriction | EMPIRICAL TEST INCONCLUSIVE |
| NVDA June 6–12, 2024, `none` and `splits` | Both HTTP/API 401 demo restriction | Split/dividend-window raw test inconclusive |
| FB and META June 8–10, 2022 | Both HTTP/API 401 demo restriction | Rename/reuse tests inconclusive |
| TWTR Oct 24–28, 2022 | HTTP/API 401 demo restriction | Terminal coverage test inconclusive |

The returned AAPL range excludes January 8; no missing-session conclusion is
drawn from an unvalidated end-date boundary. Its body SHA-256 is
`0ed88ab5343edc3c08e0f88b73e2b9e447b0a6d3006cae1f651685405ea9fd8d`.
All six API-error bodies share
`4d36d046de6d6de9487fb9a9bb6883902ac08ddb904923c7e51d37430fffca5e`.
Request durations were about 336–458 ms; bodies totaled 3,146 bytes. These are
probe measurements, not accepted workload measurements or vendor performance claims.

Exact bodies/HTTP headers, parameters, retrieval instants, hashes, documentation
and issue snapshots remain locally held under
`experiments/twelve-data-2026-10-08/`. Its observations, manifest and verification
output are not shipped by this report-only commit. The local verifier writes its
saved result when run normally; the 2026-10-15 audit intercepted that write in
memory and checked equality instead. Neither local retention nor successful
verification is a legal-entitlement finding.
The frozen manifest's inspected-input hash identifies the Stooq report version
read on 2026-10-08. That report has since received publication edits; the frozen
manifest is historical provenance, not a claim that today's report bytes match
the earlier input. The original bundle has not been regenerated.

## Every #31 gate

These are screening classifications for Basic supplying the responsibility
alone, not harness `pass/fail/unsupported` records. **PASS** requires all required
case evidence; **FAIL** requires a demonstrated conflict; **UNKNOWN** lacks enough
evidence; **EMPIRICAL TEST INCONCLUSIVE** means a bounded attempt/measurement did
not resolve the gate. There are **no full-gate PASS decisions**. Paid action
failures do not independently disqualify a price-only composite.

| Exact gate | Classification | Evidence / remaining requirement |
| --- | --- | --- |
| `historical_coverage` | EMPIRICAL TEST INCONCLUSIVE | Four AAPL dates; SPY blocked; full 2021–2026 and terminal panel untested |
| `retention_rights` | UNKNOWN | Basic duration/version retention and derived display unresolved |
| `zero_cost_feasibility` | FAIL | Required separate split/dividend endpoints are paid; composite budget unestablished |
| `regular_session_daily_ohlcv` | EMPIRICAL TEST INCONCLUSIVE | `none` documented; NVDA blocked; raw volume/session scope unknown |
| `session_calendar` | UNKNOWN | Dated schedule endpoint paid; independent calendar/bar validation absent |
| `historical_security_identity` | EMPIRICAL TEST INCONCLUSIVE | FB/META blocked; no date-scoped catalog mapping demonstrated |
| `split_handling` | FAIL | Separately attributed `/splits` excluded from Basic |
| `cash_distribution_handling` | FAIL | Separately attributed `/dividends` excluded from Basic |
| `non_cash_actions` | UNKNOWN | Original noncash coverage/terms not established |
| `terminal_events` | EMPIRICAL TEST INCONCLUSIVE | TWTR blocked; merger/spinoff/delisting evidence absent |
| `currency_units` | UNKNOWN | AAPL USD metadata observed; independent full price/volume unit validation absent |
| `missing_bar_behavior` | UNKNOWN | Missing input handling not exercised; request boundary is not a proven gap |
| `gap_backfill_behavior` | UNKNOWN | No independently expected gap/backfill experiment |
| `acquisition_catch_up` | UNKNOWN | EOD timing documented; current/downtime recovery not tested |
| `revision_correction` | UNKNOWN | No independently identified changed historical bar |
| `revision_refresh_validation` | UNKNOWN | No approved policy, explicit refresh session scope or preservation experiment |
| `repeated_retrieval_versions` | EMPIRICAL TEST INCONCLUSIVE | Unchanged AAPL body; changed retrieval case missing |
| `identity_calendar_joins` | UNKNOWN | Exact Event/session/security/SPY joins not validated |
| `deterministic_calculations` | UNKNOWN | No independent raw open/close/action calculation fixture |
| `source_disagreement` | UNKNOWN | No matched raw cross-source observation or handling experiment |
| `temporal_boundaries` | UNKNOWN | Later identity/correction exclusion and knowledge vintages not tested |
| `provenance_completeness` | UNKNOWN | Request/local time/raw bytes retained; dated identity/actions/finality absent |
| `reproducibility` | UNKNOWN | Local hash verification succeeds; required probe inputs are excluded from the commit and no full retained-input semantic adapter replay is established |
| `request_counts` | EMPIRICAL TEST INCONCLUSIVE | Eight HTTP probe requests known; complete workload counts absent |
| `elapsed_time` | EMPIRICAL TEST INCONCLUSIVE | Per-request duration retained; full workload unmeasured |
| `memory` | UNKNOWN | Required peak workload memory unmeasured |
| `storage` | EMPIRICAL TEST INCONCLUSIVE | Probe/artifact bytes counted; complete retained workload storage unmeasured |
| `workload` | UNKNOWN | Backfill/acquisition/catch-up/revision/join/calculation workload not measured |

## Composite roles and Stooq comparison

| Potential Twelve Data Basic role | Assessment |
| --- | --- |
| Established U.S. equities plus SPY historical daily price/volume inputs | Plausible candidate for `historical_coverage`, `regular_session_daily_ohlcv` and price/currency provenance; storage, raw volume, SPY/session and identity evidence required first |
| Small-panel EOD acquisition, dated catch-up and bounded rereads | Plausible contributor to acquisition/gap/retrieval/workload gates; quota arithmetic and one repeat response support investigation, not reliable operation certification |
| Current symbol/exchange/MIC/currency/type discovery | Documented catalog role; useful candidate metadata only, never authoritative historical identity intervals |
| Original splits/cash actions or dated exchange schedules | Excluded paid endpoints; cannot supply these as a free component |
| Historical security master, terminal ledger, historical vintages/finality | No defensible free role established |

A free composite would still need independently licensed original actions,
dated security/listing/lifecycle evidence and validated exchange calendars.
Application-owned preservation, joins, missingness, deterministic calculations
and replay must pass separately. This screen does not establish that sufficient
free supplements exist. Components cannot repair prohibited retention, uncertified
raw price/volume inputs, ambiguous identity or incompatible sessions by averaging
sources, reversing adjusted prices or inventing terminal returns.

Compared with the [tested Stooq route](stooq-technical-screen-2026-10-07.md),
Twelve Data documents a direct unadjusted mode, structured MIC/currency/timezone
metadata and an API/quota model. Stooq actually returned full 2021–October 6,
2026 histories for SPY/AAPL/NVDA/META; this Twelve Data probe did not. Stooq's
default was demonstrably adjusted, its skips were not certified original raw
OHLCV, its original dividend-values route failed, and ordinary TWTR lookup was
unavailable. Twelve Data has stronger documented price/metadata controls but
weaker empirical coverage here; its separate actions are definitively paid.
Neither route has cleared raw regular-session semantics, historical identity,
terminal coverage, retention rights or the complete contract. Stooq's technical
screen did not assess legal rights; do not treat it as legally safer by default.

## Decision and smallest next action

- **Can Basic satisfy #31 alone? No:** separate split/cash-action entitlement fails.
- **Composite?** Plausibly prices/SPY, EOD acquisition/catch-up/rereads and current
  metadata, conditional on unresolved rights and semantic validation; no role is
  cleared for reliable Signal use yet.
- **Hard FAIL:** Basic split/cash endpoints and hence all-in-one zero-cost
  feasibility. Dated schedule access is also paid. Other gates remain unknown or
  empirically inconclusive as listed; no raw/session or delisted failure was inferred
  from a demo rejection.
- **Legal/storage terms themselves disqualifying? Not established as a blanket
  active-Basic ban.** They remain a blocking UNKNOWN; termination obligations are
  explicit. Raw display is outside advertised Basic entitlement, while derived
  Analysis display needs clarification. A confirmed incompatibility would reject
  even the price component.
- **Further empirical testing justified? Only a small authenticated Basic price
  probe after legal/entitlement clarification.** No broad backfill or paid action
  experiment is justified for the always-free requirement.
- **Smallest next action:** obtain written Basic-specific confirmation covering
  indefinite local raw/revision retention while active, derived retention/private
  Analysis display, applicable third-party limits and termination handling. Include
  whether `adjust=none` daily OHLCV/volume is strictly regular-session-only and
  whether confirmed EOD status is exposed. No provider message was sent. If rights
  are compatible, use a Basic key for a tiny SPY/AAPL/NVDA/FB→META/TWTR panel with
  independent action/calendar expectations; otherwise stop this route.

Production market readiness and #31 are unchanged.
