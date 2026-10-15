# Bounded Stooq technical screen against Signal V2 #31

Observation date: **2026-10-07**. Experiment only. **Stooq remains plausible as
an active-security price component, but the tested free route does not satisfy
the full Signal market-data contract.** Original cash-action values fail directly;
historical ticker lookups are unsafe without independent dated identity mappings;
TWTR history was unavailable at its ordinary symbol; and two identity-test ETFs
have missing dates. Regular-session semantics and genuinely original unadjusted
OHLCV remain unestablished, including with the visible adjustment skips.

Publication review, **2026-10-15**: this independently authored report and the
[independent event/calendar references](stooq-event-source-check-2026-10-07.md)
can stand separately from the original experiment bundle. The bundle remains
locally held and excluded from the proposed commits because retention and
redistribution rights are unresolved. Provider price/volume examples and a
provider-text quotation have been removed from this report; the dated methods,
aggregate technical observations and limitations remain. No permission is
inferred from successful retrieval or replay. The committed report alone does
**not** provide offline reproduction of the experiment.

No provider was integrated, no production readiness was activated, no application
or database state was changed, no issue was edited, and no Git operation was
performed. Legal/storage permission is intentionally unassessed. Empirical local
retention below does not establish rights. This is a screening report, not a
`MarketConformanceApplication` acceptance report or provider approval.

The first inspections were [#31](https://github.com/AviSharma01/signal-workspace/issues/31)
and its [provider-neutral conformance contract](../market-data-conformance.md),
the market requirements of [#26](https://github.com/AviSharma01/signal-workspace/issues/26)
and [§6 of the approved specification](../specs/signal-v2.md), and the
[prior free-provider screen](free-market-data-provider-screen-2026-10-07.md).
Those inspected inputs are retained alongside the experiment. The unchanged
contract requires original regular-session daily OHLCV, separate actions,
historical identity, aligned sessions, retained observed revisions, and replay.
Provider-adjusted prices alone cannot pass. The experiment does not reconstruct
what Stooq knew in 2021 from bytes first observed in October 2026.

Success criteria were a small independently anchored panel, retained exact input
bytes and hashes, reproducible offline comparisons, and an explicit classification
for every contract gate. The plan was contract inspection → independent event
references → bounded downloads → offline measurements → gate decisions.

All original experiment code and inputs remain locally held under
`experiments/stooq-2026-10-07/`, outside application imports, normal data
directories and production persistence. Its README, manifest, measurements,
verification results, browser transcriptions, downloaded inputs and frozen
reference copies are **not included in the report-only commit**. Their paths
are recorded as local inventory, not links promised to repository readers.
CSV/body/header files are exact bytes; browser text is explicitly a transcription,
not a raw HTML snapshot. Original download file mtimes provide local completion
proxies, not vendor publication timestamps or finality.

The evaluation boundary is **2026-10-06**, the latest completed US session when
these requests were made before the October 7 open. The requested daily interval
was 2021-01-01 through that boundary, plus one ten-session action window and one
seven-session catch-up window. There were twelve CSV exports, not a market-wide
backfill. No bulk archive, account creation, CAPTCHA solving, or paid access was
used. AAPL's UI advertises history beginning September 7, 1984, but that older
range was not downloaded or certified.

| Sample / observed current Stooq identity | Returned span | Rows | Calendar observations |
| --- | --- | ---: | --- |
| SPY — State Street SPDR S&P 500 ETF Trust | 2021-01-04–2026-10-06 | 1,446 | No missing, duplicate or unexpected dates |
| AAPL — Apple Inc | same | 1,446 | Same exact dates as SPY |
| NVDA — NVIDIA Corp | same | 1,446 | Same exact dates as SPY |
| META — Meta Platforms Inc | same | 1,446 | Same exact dates as SPY, including former FB period |
| METV — Roundhill Ball Metaverse ETF | 2021-07-01–2026-10-06 | 1,319 | Missing 2025-05-22, 05-23, 05-29 within returned span |
| FB — ProShares S&P 500 Dynamic Buffer ETF | 2026-07-01–2026-10-06 | 56 | Twelve missing dates within returned span; no 2025 data returned |
| TWTR — attempted terminal security | unavailable | — | UI says symbol does not exist in database |

ETFs other than SPY are identity stress cases, not proposed Analysis assets.
Only the four established names pass the bounded date/depth check. METV starts
after its June 30, 2021 launch; first-day completeness was not assumed. FB's
issuer reports June 24, 2025 inception, distinct from listing/first-trade date;
the export starts over a year later. Missing rows establish missing inputs, not
why they are absent or whether trades occurred on each date. No values were filled.
The twelve FB gaps are 2026-07-16, 07-29, 08-13, 08-20, 08-24, 08-25, 08-27,
08-31, 09-01, 09-08, 09-09 and 09-15.

The independent ICE/NYSE calendar yields session counts of **252 / 251 / 250 /
252 / 250 / 191** for 2021–2026 through the boundary. All four established
histories exclude weekends, scheduled holidays, and the extraordinary
2025-01-09 Carter closure. They include all ten early-close dates through the
boundary, including 2024-07-03, 2024-11-29 and 2024-12-24. There are no invalid
OHLC orderings, duplicate dates, or nonpositive volumes in downloaded rows.
These are positive date/schema observations; they do not establish bar timestamps,
09:30–16:00 coverage, early-close cutoff, DST treatment or exclusion of extended
hours. CSV supplies `Date,Open,High,Low,Close,Volume`, without timezone, venue,
currency, security identifier, action, finality or revision fields. Exchange
calendar dates are independently referenced in the companion source note.

The highest-risk action check uses NVIDIA's **10:1 split**, first adjusted
trading **2024-06-10**, and **$0.01** post-split dividend with **2024-06-11
ex-date**. These dates and terms come from the
[issuer's June split FAQ](https://investor.nvidia.com/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf),
not Stooq. The split timing is also recorded in
[NVIDIA's SEC 8-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581024000144/nvda-20240607.htm).
AAPL's 2020 4:1 split and May 2024 dividend were independently researched, but
the 2020 window was not downloaded and Apple's original May ex-date could not
be verified from accessible primary sources. They are not passed tests; NVIDIA
provides the actually inspected, primary-verified split and dividend case.

**The default route is demonstrably adjusted.** It puts pre-split NVIDIA on
the later share basis. Split/dividend skips reverse that scale discontinuity and
change historical OHLCV. All ten NVIDIA comparison rows differ. SPY's dividend
skip changes 1,058 of 1,446 rows. Skipping AAPL splits alone changes no rows in this post-2020
window, as expected; that is not a test of its 2020 split.

**The skip route is not certified original raw data.** NVIDIA's skipped full
history has 987 fractional-volume rows and SPY's 1,058. Price values have many
decimal places. The paired exports are consistent with reversing provider
adjustments, including inverse volume changes. That is an inference, not proof
of the provider's algorithm or feed. Without separately verified original OHLCV
and field definitions, these values cannot be declared original prices/traded
share counts, rounded into purported raw values, or accepted as regular-session
data. Nasdaq's accessible historical price page returned unavailable data in
the independent price-check attempt. No secondary adjusted price series was used
as the expected raw-price oracle.

**Original cash amounts fail for the inspected operations-table route.**
[Stooq's NVIDIA operations page](https://stooq.com/q/m/?s=nvda.us) correctly
identifies the June 10 split and June 11 dividend, but the inspected nominal
amount differs from the issuer's original `$0.01`. Its footnote explains
that historical nominal values are recalculated with subsequent operations.
The table's latest visible action is December 5, 2024, despite October 2026
prices; action freshness/completeness is therefore unestablished independently
of price reachability. Separate authoritative supplements might supply original
terms, but none is certified as a complete action ledger by this experiment.
The split date/ratio subcheck passes; complete split treatment with verified raw
prices, units, attribution and availability remains inconclusive.

**Historical literal tickers are unsafe.** Meta's
[issuer announcement](https://investor.atmeta.com/investor-news/press-release-details/2022/Meta-Platforms-Inc.-to-Change-Ticker-Symbol-to-META-on-June-9/default.aspx)
and [Nasdaq notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2022-125)
establish FB→META before open June 9, 2022, with unchanged CUSIP. Stooq `meta.us`
returns a continuous 2021 history, including the former FB period.
Separately, [Roundhill](https://www.roundhillinvestments.com/etf/metv/) and
[OCC memo 49960](https://infomemo.theocc.com/infomemos?number=49960) establish
the ETF's former META symbol and META→METV at open January 31, 2022. Stooq
`metv.us` also returns a distinct July 2021 history. Thus the two current symbols expose
distinct histories, but a historical disclosure containing literal META in
July 2021 cannot safely be joined to today's `meta.us`. The CSV does not supply
dated ticker-to-security validity intervals. Two numerically distinct files are
not a historical identity contract.

There is a second observed reuse hazard: `fb.us` now identifies the
[ProShares FB ETF](https://www.proshares.com/our-etfs/strategic/fb), CUSIP
74349Y613, inception June 24, 2025, corroborated by
[Cboe](https://www.cboe.com/us/equities/listings/listed_products/symbols/FB).
It does not retrieve Facebook's old history. Ordinary former-ticker lookup
therefore fails the historical-identity join route. Alternative archived symbols
or a complete dated mapping service were not established; their existence
remains UNKNOWN.

**Terminal history is unavailable for the selected ordinary TWTR route.**
Its history page reported that the ordinary symbol was absent from the database. The
[NYSE-signed Form 25](https://d18rn0p25nwr6d.cloudfront.net/CIK-0001418091/8f906d28-b15e-432d-b2ee-4744709b40cf.pdf)
independently establishes merger October 27, 2022, suspension before open
October 28, and actual listing removal November 8. These are separate dates.
No TWTR bars or Stooq terminal metadata were obtainable through this route.
This is a concrete sampled-route failure, not proof that every possible Stooq
archive lacks TWTR or all delisted securities. No $54.20 settlement was converted
into a numeric terminal return; under §6 that treatment remains unapproved.

Repeated retrieval and local replay have positive bounded evidence in the
excluded local bundle; these are historical local results, not runnable
capabilities of the report-only repository packet:

- AAPL identical default request downloaded twice, approximately 29.5 minutes
  apart, yields identical 75,483-byte files and SHA-256
  `8156bfb10d534f24df85114c7046c96da064a63aef526fb41dff3601bbfdbce4`.
  All 1,446 rows agree semantically. Each observation is retained separately.
- NVIDIA's separate ten-session request with identical skip settings matches
  the overlapping full-history rows exactly. Changes from *different adjustment
  settings* are not classified as revisions.
- SPY's September 28–October 6 catch-up export returns seven expected sessions,
  all semantically equal to the corresponding retained full-history rows.
  It includes October 6, so one-session presence is verified, but a separately
  timed daily publication/finality acquisition was not tested.
- Three direct GETs (two `.com`, one `.pl` through Stooq's linked alternate
  surface) returned HTTP 200 with 796-byte browser-verification HTML instead
  of CSV. Exact bodies and headers are retained. HTTP success is not data success;
  nonce/body differences are not market-data revisions. A prior HEAD likewise
  returned verification-page headers. Sandbox DNS failures were excluded from
  provider measurements.
- Hash/semantic comparison detects byte or row changes, and separately named
  files preserve prior retrieved bytes. The verifier checks hashes of all 25
  retained input/reference artifacts, replays the parser twice without network,
  and compares both outputs with saved measurements. Its in-memory altered-close
  self-check detects a synthetic change without touching original files. **No
  actual changed vendor price version was observed.** A live correction and
  practical refresh cadence remain EMPIRICAL TEST INCONCLUSIVE/UNKNOWN.

The retained CSVs total **660,515 bytes**; all 25 hashed input/reference artifacts
total **822,116 bytes**. This excludes scripts, manifest and derived reports.
The manifest retains exact sizes/hashes, request settings and local completion
times for each input. Repeated-byte retention is demonstrated, not legally
approved. Offline parsing covers 11,524 returned rows including repeated and
overlapping observations, not that many independent security sessions.

Workload results are bounded observations, with no approved performance target:

| Workload | Measured evidence | Limit |
| --- | --- | --- |
| Four established-name history exports | 4 requests, 5,784 rows; approximately 70–116 KB per file depending on skip precision | Not a universe/backfill coverage audit |
| Seven-session SPY catch-up | 1 export, 7 rows, 380 bytes, exact overlap | No real downtime/failure recovery or scheduling test |
| Repeat retrieval | 1 additional full AAPL export; no changed version | Actual revision/correction unobserved |
| Direct HTTP GET attempts | 3 calls; 0.987, 1.481 and 1.098 seconds; HTML each time | No usable unattended CSV acquisition demonstrated |
| Browser exports | 12 successful CSV exports; associated tool calls about 3.3–464.2 seconds | Entire automation calls, not HTTP latency; include UI/runtime waiting |
| Two offline parser/replay runs | Verified run approximately 348 ms and 10,783,295 peak traced Python allocation bytes | Excludes browser memory, native allocation and full process RSS |

The CSV export count and deliberately initiated direct requests are known; total
HTTP traffic from browser challenges/assets/download internals was not captured.
Consequently the full request-count gate remains UNKNOWN. Main-page navigation
and form-submission counts in the manifest are descriptive tool observations.
No concurrency/rate-limit stress test was run. Bulk ZIP size/limits and a reliable
unattended route remain UNKNOWN. If a usable single-symbol route existed and
scaled linearly, N securities plus SPY would require roughly N+1 bounded exports
for initial backfill and N+1 for each same-route daily/catch-up batch; the sampled
history storage scale would be roughly 70–116 KB per established instrument per
observed version. These are conditional workload estimates, not a measured quota,
latency projection, approved refresh policy or production feasibility claim.

Every #31 gate is classified below. **PASS is limited to the stated experimental
scope.** A passed subcheck does not make a multi-case contract gate pass. UNKNOWN
means missing semantics/evidence or deliberately untested scope; EMPIRICAL TEST
INCONCLUSIVE means the performed probe did not decide the complete gate. FAIL
identifies the tested route/case, not every hypothetical supplement/archive.

| Exact #31 gate | Classification | Evidence and remaining boundary |
| --- | --- | --- |
| `historical_coverage` | FAIL | Four established names PASS 2021–boundary date completeness; selected panel fails due FB/METV missing inputs and TWTR absence. Universe completeness not established. |
| `retention_rights` | UNKNOWN | Intentionally outside this empirical task. |
| `zero_cost_feasibility` | UNKNOWN | These requests required no payment; required complete access plus retention permission not established. |
| `regular_session_daily_ohlcv` | UNKNOWN | Default adjusted route FAIL; skips differ but original raw prices/volume, feeds and exclusion of extended hours unverified. |
| `session_calendar` | UNKNOWN | Holiday/date and ten early-close-date presence subchecks PASS; early-close time and DST/timezone bar boundaries absent. |
| `historical_security_identity` | FAIL | Ordinary literal FB/META route unsafe under independently verified reuse; complete dated mappings/listing-change/ambiguity behavior missing. |
| `split_handling` | EMPIRICAL TEST INCONCLUSIVE | NVDA 10:1 date/ratio subcheck PASS; share-scale response visible; original raw OHLCV/economic treatment not independently certified. |
| `cash_distribution_handling` | FAIL | Tested original nominal amount disagrees with issuer $0.01 and is explicitly recalculated. |
| `non_cash_actions` | UNKNOWN | No bounded noncash-action sample; no treatment inferred. |
| `terminal_events` | FAIL | TWTR ordinary history unavailable; no terminal-action feed demonstrated; spin-off untested. |
| `currency_units` | UNKNOWN | CSV supplies no currency/price/volume definitions; fractional-volume skip outputs unresolved. |
| `missing_bar_behavior` | UNKNOWN | Experiment exposes exact gaps without fills; no application adapter/fail-closed use semantics implemented or tested. |
| `gap_backfill_behavior` | EMPIRICAL TEST INCONCLUSIVE | Bounded SPY gap/catch-up window matches; full METV/FB requests still omit session dates, reasons and recoverability unestablished. |
| `acquisition_catch_up` | EMPIRICAL TEST INCONCLUSIVE | Seven-session retrieval PASS; unattended daily acquisition, finality and real downtime recovery unestablished. |
| `revision_correction` | EMPIRICAL TEST INCONCLUSIVE | Real repeated/overlap observations stable; hash detector self-check is synthetic, no later vendor correction observed. |
| `revision_refresh_validation` | UNKNOWN | No approved policy, measured correction cadence or complete refresh evidence. |
| `repeated_retrieval_versions` | EMPIRICAL TEST INCONCLUSIVE | Unchanged-request subcase PASS; changed vendor version not observed. |
| `identity_calendar_joins` | FAIL | Date-set join passes for four established names; historical ticker/security join cannot safely follow literal META/FB. Exact timestamp anchor join unestablished. |
| `deterministic_calculations` | EMPIRICAL TEST INCONCLUSIVE | Decimal example/replay deterministic; independent original raw-price oracle unavailable, so contract's representative calculation expectation not certified. |
| `source_disagreement` | UNKNOWN | No independently verified second raw OHLCV feed; no averages or stitching performed. |
| `temporal_boundaries` | UNKNOWN | These October 2026 observations cannot establish earlier identity/correction availability. No application temporal conformance execution. |
| `provenance_completeness` | UNKNOWN | Exact bytes, settings, observation completion proxies/hashes retained; feed, units, session timestamps, mappings, action availability and finality incomplete. |
| `reproducibility` | PASS | Locally held exact inputs reproduced this experiment's parser/measurements offline twice. Required inputs/scripts are excluded from the commit, so the published repository cannot replay it. Complete adapter semantic replay remains untested; no conformance capability is authorized. |
| `request_counts` | UNKNOWN | 12 export initiations and 4 successful direct HTTP initiations recorded; full browser network counts unavailable. |
| `elapsed_time` | PASS | Finite measured direct/tool-call and offline parser times, with explicit scopes; no provider SLA inference. |
| `memory` | PASS | Actual bounded offline replay Python allocation measured; network/browser/full-application memory untested. |
| `storage` | PASS | Exact local artifact byte counts and SHA-256 integrity verified. |
| `workload` | EMPIRICAL TEST INCONCLUSIVE | Small backfill/catch-up/repeat/date-join/parser/calculation observations retained; revision workload and complete safe historical identity joins unavailable. |

Thus exact full experimental gate PASS names are **`reproducibility`,
`elapsed_time`, `memory`, `storage`** with the scope limitations above. No complete
semantic/session/action/identity gate is passed. Useful positive subchecks are
active-name depth/date alignment/schema sanity, holiday absence, early-close
date presence, NVDA split date/ratio, unchanged AAPL retrieval, overlapping
NVIDIA retrieval and seven-session SPY catch-up equality. These are not broader
readiness claims.

**Decision:** keep Stooq as a limited technical lead for an active-name composite,
not as a complete standalone provider. Hard sampled-route failures are the
adjusted default price route, recalculated original dividend amount, unsafe
literal historical ticker resolution, unavailable TWTR history, and incomplete
selected ETF date coverage. Supplements would need independent completeness and
join validation. None of these is repaired by licensing permission alone.

**Waiting for licensing clarification is worthwhile only as a low-cost parallel
lead.** It should not delay other provider work or trigger a larger Stooq backfill.
The remaining technical clarification needs a supported raw export/feed/volume
definition and a route to dated identity/terminal history, not merely archive
permission. The highest unknowns are original skip-export OHLCV, regular-session
and early-close boundaries, units/feed coverage, historical mapping/archive
availability, unattended downloads and quotas, original complete action coverage,
corrections/finality and usable refresh cadence.

**Smallest next experiment:** if a supported raw/session definition is obtained,
use only SPY and NVDA for June 7, 10 and 11, 2024, plus the July 3, 2024 early
close, comparing both settings against an independent authoritative original
regular-session OHLCV source with volume definitions. Test one supported
unattended retrieval and one later repeat. Stop if volume/feed semantics conflict;
do not expand the universe. TWTR and historical mappings need a concrete archive
route before further guessing/probing. If no raw/session route is identified,
no additional price experiment is justified yet.
