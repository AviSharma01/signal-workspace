# Bounded market-data contract validation

Research session: 2026-09-17 Asia/Kolkata (2026-09-16 UTC). Evidence only; no provider approval. Checkout inspected: `8c120b93a8a54b8e56efb572882a7f5460ce4e16`.

Addresses [Validate candidate market-data providers against the minimum contract](https://github.com/AviSharma01/signal-workspace/issues/13), using the canonical [approved minimum contract](https://github.com/AviSharma01/signal-workspace/issues/10#issuecomment-5700881687). The [earlier evidence](market-data-source-evidence-2026-09-15.md) is a starting point, not renewed entitlement proof.

## Scope declared before probes

Candidates: Yahoo through yfinance, Alpaca Basic, Massive Stocks Basic, and Alpha Vantage free. Public-access-only review: no account creation, paid subscriptions, credential discovery, authenticated requests, application changes, or source-data writes. At most two public/demo market requests per candidate; documents are separate. Initial intended cases were ordinary AAPL, NVDA's 2024 split, FB→META rename, TWTR delisting, and official holidays/early closes. IBM replaces AAPL only as a public demo access control; this is not a substitution in an Event or analysis. No bulk panel was attempted. The required historical interval starts 2021-01-01 and extends through completed sessions in 2026; the preferred STOCK Act era remains additional scope, not a substitute for the minimum.

The practical stop condition was useful bounded evidence plus explicit unresolved validations, not exhaustive vendor discovery. Retained research samples would be isolated in `/tmp`; none were retained as local raw data. Web-tool representations are observations, not byte-preserving provider-response archives. No production data was touched. The report is preserved on `research/market-data-contract-validation`.

## Main findings

No candidate is established as satisfying the complete zero-cost contract. Two concrete access/semantic obstacles are stronger than generic unknowns:

- Alpha Vantage's current [daily API documentation](https://www.alphavantage.co/documentation/) says raw daily `outputsize=full` requires premium access; the free compact option supplies 100 points. Therefore the advertised 25+ years does not provide the required free initial history through this endpoint.
- Alpaca's [aggregation rules](https://docs.alpaca.markets/us/docs/market-data-faq) allow extended-hours conditions T and U to update daily volume while excluding them from daily OHLC. Its standard daily OHLCV therefore does not establish the required all-field regular-session semantics. A time-series granularity named daily cannot resolve this mismatch. Massive's [hours FAQ](https://massive.com/knowledge-base/article/does-massive-offer-pre-market-and-after-hours-data) likewise describes aggregates covering extended hours without a regular-hours-only parameter.

These are findings about specified paths, not proof no alternative product can satisfy the contract. Filtering/aggregating intraday data is not silently approved as a remedy: the contract requires a later approved need for intraday acquisition. Any alternative must preserve feed, eligibility and session semantics and be independently validated.

## Requirement-by-candidate matrix

**D** = documented capability only; **O** = observed narrow sample; **F** = documented mismatch for evaluated path; **U** = unverified. None means accepted. Earlier document-level findings are identified explicitly rather than presented as fresh runtime checks.

| Requirement | Yahoo / yfinance | Alpaca Basic | Massive Basic | Alpha Vantage free |
|---|---|---|---|---|
| 2021–2026 daily initial history | U: long history interface in earlier review; public probe blocked by tooling | D: plan advertises history since 2016; U per-security/account coverage | F: current plan advertises two years | F: full daily premium; compact 100 points |
| Preferred 2012 onward | U | F for advertised since-2016 path | F for Basic | F for free compact path |
| Raw daily OHLCV | D: library controls; original units/adjustments U | D: raw adjustment option; full session semantics F below | D: unadjusted flag; full session semantics U/F below | D; O demo exposes separate OHLCV fields |
| Regular-session inclusion, OHLCV definitions | U: `includePrePost=false` alone does not certify provider definitions | F: extended-hours daily volume documented | F/U: extended-hours aggregates; no validated regular-session daily alternative | U: raw daily label does not settle all trade/session rules |
| Feed/venue, currency, units | U complete semantics | D IEX vs SIP distinction; U chosen-account delayed SIP entitlement and all required units | D broad feed in earlier review; U sampled field equivalence | U feed/venue and all required unit semantics |
| Delisted/security history, rename/reuse | U; no successful lifecycle sample | D `asof` identity mapping in earlier review; U lineage and knowledge availability | D historical/inactive ticker metadata in earlier review; U sample and Basic entitlement | D historical listing status in earlier review; U delisted price history and lineage |
| Corporate actions and terminal events | D splits/dividends interface; U completeness, mergers/spin-offs/terminal evidence | D separate action endpoint; U completeness/availability; timing not guaranteed | D split/dividend endpoints; U full lifecycle and Basic history | D adjusted endpoint/action fields premium; U sufficient free independent actions |
| Calendar, timezone, session-date compatibility | U | U runtime validation | U runtime validation | O four NYSE holiday exclusions only; U full calendar/early close/DST |
| Missing bars vs failed retrieval | U: tooling block is not missing price evidence | D bar omission rules; U measured missingness | D no eligible trades may omit bars in earlier review; U measured missingness | O narrow demo dates; U panel coverage and cause attribution |
| Corrections, snapshot versions, finality | U | D updated bars/corrections; U bounded historical refresh | U validated refresh | U validated refresh |
| Source/retrieval provenance | U retained raw response and all identity/action inputs | D explicit feed/request controls; U complete provenance capture | D request parameters; U complete capture | O symbol, refresh date, timezone; U source revision/publication time |
| Local retention sufficient for reproducibility | U; software license does not license data | U account/data agreements not verified | U applicable individual-data agreement not established | U inspected terms do not establish required archival rights |
| Compatible fallback / cross-provider windows | U: no matched comparison | U: no matched comparison | U: no matched comparison | U: no matched comparison |
| Daily/catch-up operational feasibility | U measured request/error/storage profile | D quotas/pagination; U end-to-end trial | D quota; U end-to-end trial; initial coverage F | D compact could catch short gaps; F initial history, U operational breadth |
| Full zero-cost acceptance | U, not certified | U plus documented daily-volume mismatch | F evaluated Basic history | F evaluated free daily history |

Current [Alpaca plan documentation](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api) and [Massive pricing](https://massive.com/pricing) were revisited. No account entitlement was tested. Alpaca's historical SIP access distinction remains as described in its [FAQ](https://docs.alpaca.markets/us/docs/market-data-faq); live free IEX and delayed historical SIP are not interchangeable evidence. An authenticated explicit-feed request is still required. Identity `asof` is not a database-vintage replay.

## Executed observations and independent checks

Two market-data URL opens were attempted through the web tool. Search/document fetches are not included in that count. No direct HTTP timing, status headers, response hash, peak memory, byte count, or provider latency is available from this mechanism; tool wall time would not measure provider performance. No authenticated Alpaca or Massive request was attempted because access was deliberately public-only. No denial response was observed for those two candidates.

| Probe | Reproduction URL / parameters | Observed result |
|---|---|---|
| Yahoo NVDA split window | `https://query1.finance.yahoo.com/v8/finance/chart/NVDA?period1=1717632000&period2=1718150400&interval=1d&events=div%2Csplits&includePrePost=false` | Web tool returned non-retryable URL-safety error. No provider response obtained; not a provider outage or evidence of missing NVDA history. |
| Alpha Vantage public demo | [IBM daily demo](https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo) | Rendered JSON metadata: IBM, Compact, US/Eastern, last refreshed 2026-09-15. Visible range 2026-04-23–2026-09-15. Returned OHLCV fields. Demo access is not a free user's general entitlement or production feed reliability proof. |

Independent expected holiday dates came from [NYSE's official 2026 calendar](https://www.nyse.com/trade/hours-calendars), not Alpha Vantage: May 25, June 19, July 3, September 7. Manual inspection of the rendered IBM JSON found each absent and the adjacent sessions present: May 22/26, June 18/22, July 2/6, September 4/8. **Four of four holiday-exclusion spot checks matched.** This is date-membership evidence only. It neither measures all expected sessions nor proves full-panel completeness, regular-session volume, numerical OHLC correctness, or that data was available on those dates. The demo's latest date is reported as observed; no freshness SLA is inferred.

The following independent expectations define the remaining bounded fixtures; they were not executed as provider acceptance tests:

| Case | Expected evidence / assertion | Outcome here |
|---|---|---|
| Ordinary session | Independent same-feed exchange/issuer reference for raw OHLCV; exact declared rounding | Demo fields observed, numerical truth U; no independent numerical source obtained |
| Early close | NYSE lists 2026-11-27 and 2026-12-24 closing at 13:00 ET; retain session with shorter duration | Future at research time, no market sample; historical early-close fixture still needed |
| Timezone / DST | Applicable exchange opening/closing instant mapped using America/New_York; never fixed EST offset year-round | No provider timestamp comparison executed |
| Split | [NVIDIA SEC filing](https://www.sec.gov/Archives/edgar/data/1045810/000104581024000144/nvda-20240607.htm) establishes 10-for-1 split and adjusted trading expected June 10, 2024 | Independent ratio/date established; Yahoo comparison blocked. Do not expect next-day raw close to equal exactly one tenth of prior close because trading moves prices |
| Rename and ticker reuse | FB→META needs issuer/exchange effective-date evidence; reuse additionally needs two distinct issuer/listing identities | Not fetched/compared; no historical join approval |
| Merger, spin-off, delisting | TWTR and a declared spin-off need independent terminal/listing/action records and dated terms; never invent continuation prices | Not fetched/compared; sample scope narrowed after access limits |
| Missing bar / ambiguous join | Controlled absent session and two plausible identities must leave measurement unavailable while retaining Event | Contract-derived expected invariant; subsystem test not executed |
| Changed historical bar / temporal leakage | Two snapshots preserve both inputs/results; later correction cannot alter prior predictor/eligibility/evidence | No repeat snapshot or application path tested; unverified |

The four holiday checks are the only completed independent provider comparisons. Other expectations are a validation backlog, not passing tests. No denominator for the required historical panel was established; coverage percentage, missing-bar count and instrument-level completeness are **unmeasured**, not zero.

## Acquisition, catch-up and bounded revisions

Documentation establishes ways to request history, not validated operation. Alpaca's [historical bars interface](https://docs.alpaca.markets/us/reference/stockbarsingle-1) supports date bounds and pagination; the earlier review records endpoint-specific limits for other candidates. For a later access-enabled trial, declare a small fixed listing panel, exact dates, feed, raw adjustment settings and expected exchange sessions before acquisition. Record every page, attempt, error and request parameter; compare expected sessions with observed rows, classifying closed session, pre-listing/post-termination, unavailable data and failed request separately. Do not fill gaps or drop Events.

A minimal operational experiment would acquire the declared panel, deliberately omit several completed sessions, then catch up from the last covered session and independently reconcile the expected-calendar set. Repeat one identical request and one historical overlap request while preserving first responses. Report observed request counts, elapsed time, memory and bytes, and distinguish unchanged retrievals from changed versions. This experiment was **not performed**, and no running acquisition/catch-up behavior is certified.

A bounded revision-refresh candidate to test—not an approved policy—is a recent fixed session overlap on each daily run plus a quota-bounded rotation through older retained chunks. Specify the overlap length, chunk size and revisit interval only after measuring available quota and correction behavior. Compare raw logical values and separately preserve request observations. Include an injected old correction outside the recent overlap to demonstrate the limitation; never claim all revisions captured. [Alpaca action documentation](https://docs.alpaca.markets/us/reference/corporateactions-1) warns that creation timing is not guaranteed, so economic/action dates cannot serve as first-availability evidence.

Feasibility limits: Alpha Vantage compact can conceptually recover a short recent gap, but cannot establish the required initial history and cannot recover arbitrary downtime beyond its accessible window. Massive Basic cannot backfill 2021. Alpaca's documented history length could support the time span, but daily-volume semantics and actual entitlement remain unresolved. Yahoo access/reliability and semantics remain unverified. There is **no validated bounded refresh policy for any candidate** from this session.

Initial backfill, catch-up and revision-refresh workloads have no measured provider-performance results here. Event-to-session and security-resolution joins also remain unmeasured; no production implementation was exercised. Cohort/outcome workload measurements await approved methods. No Python/q choice, benchmark, return formula or event window was selected.

## Retention and adoption blockers

[Alpha Vantage terms](https://www.alphavantage.co/terms_of_service/) describe personal/non-commercial use and a revocable access license; this review did not establish permission to retain every computation input and historical revision after access ends. [Massive's legal index](https://massive.com/legal/terms) distinguishes website, individual and business terms; merely reading pricing or the website terms cannot certify data retention. Alpaca's applicable account/feed agreements were not obtained. The [yfinance project notice](https://github.com/ranaroussi/yfinance) distinguishes its software from Yahoo data rights. No legal conclusion about permitted archival use is asserted.

Before adoption, obtain the applicable data agreement and explicit evidence for local raw-response/input retention, prior revisions, action/identity records, and use after termination sufficient to reproduce results. Where terms do not answer, seek provider clarification. No data license was accepted or paid service acquired here.

The next [Choose historical and ongoing market-data source strategy](https://github.com/AviSharma01/signal-workspace/issues/14) decision must treat these as evidence gates, not quietly relax the minimum: full historical/identity panel access, all-field session/feed compatibility, retention permission, independent lifecycle fixtures, measured catch-up and bounded refresh, and explicit handling of uncovered measurements. No cross-provider comparison established compatible fallback; source disagreements and deterministic input selection remain unvalidated. This session establishes concrete mismatches and a small public calendar observation; provider acceptance remains unproved.
