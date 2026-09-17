# Bounded alternative market-data prerequisite screen

Research observation date: **2026-09-17**. Evidence class: documentation research
and public-document access observations, not operational validation or an approved
provider decision.

## Scope and outcome

**None of the three fixed candidates clears all six prerequisites.** EODHD Free
and Marketstack Free explicitly fall short of the historical minimum. Twelve
Data Basic has useful access and historical-data documentation, but its complete
retention, daily-session semantics, and reproducible-input provenance requirements
remain unverified. This is a feasibility blocker for this bounded pass under the
unchanged contract; it does not establish that no possible zero-cost source exists.

The work answers [Screen up to three additional zero-cost market-data
sources](https://github.com/AviSharma01/signal-workspace/issues/21), following its
[pre-probe scope declaration](https://github.com/AviSharma01/signal-workspace/issues/21#issuecomment-5709825149).
The fixed set was Twelve Data Basic, EODHD Free, and Marketstack Free; none was
replaced. Yahoo/yfinance, Alpaca, Massive, and Alpha Vantage were excluded.

Acceptance follows the approved [minimum reliable market-data
contract](https://github.com/AviSharma01/signal-workspace/issues/10#issuecomment-5700881687)
and [research objectives and operating
constraints](https://github.com/AviSharma01/signal-workspace/issues/2#issuecomment-5677296093).
The minimum now means complete calendar years **2021–2025 plus 2026 to date**,
with explicit coverage limits. A rolling year cannot satisfy it. Retention means
preserving the actual source inputs used and earlier versions/results sufficiently
to reproduce computations; it does not require redistribution rights or capturing
every revision ever published.

The cap was six unique primary-document URLs per candidate, including failed
attempts, eighteen total. Searches were used only to locate Twelve Data's two
remaining support pages. Incidental search results were not adopted as additional
sources or candidates. Re-reading sections of an already counted page did not
expand that inventory. No accounts, keys, purchases, data API samples, bulk
downloads, or operational trials were used. No provider was selected.

## Classification

**Supported** means the cited documentation supports that screen requirement at
the stated scope; it does not certify observed performance. **Failed** means an
explicit documented incompatibility. **Unknown/unverified** means insufficient
evidence within this pass, including ambiguous applicability or retrieval failure.
Every requirement must be supported to clear the screen.

| Requirement | Twelve Data Basic | EODHD Free | Marketstack Free |
|---|---|---|---|
| Documented access path | Supported | Supported | Unknown/unverified |
| Zero-cost feasibility under operating constraints | Unknown/unverified | Failed | Failed |
| Retention/storage sufficient for contract | Unknown/unverified | Unknown/unverified | Unknown/unverified |
| Daily-bar/session semantics and feed scope | Unknown/unverified | Failed | Unknown/unverified |
| Provenance sufficient for reproducible retained inputs | Unknown/unverified | Unknown/unverified | Unknown/unverified |
| Documented historical coverage against minimum | Supported, advertised daily-history scope only | Failed | Failed |

### Twelve Data Basic

- **Access — supported.** The historical-price guide documents `/time_series`
  with an API key, `1day`, date bounds, and output-size controls. Its examples
  establish an access path, not a successful request in this investigation. [T5]
- **Zero cost — unknown/unverified.** Basic is advertised at $0 with 800 daily
  credits and internal non-display use. These limits do not establish adequate
  daily acquisition, catch-up, revision refresh, actions, and historical identity
  coverage for this workspace; no workload was measured. [T1]
- **Retention — unknown/unverified.** Terms §2.2 permits internal storage, but
  §2.3(g) defers cache duration to documentation; §16.1 conditions retention on
  subscription and third-party restrictions. Sections 12.5 and 16.2 require data
  deletion after termination/expiration (the latter within 30 days), with a
  compliance-audit exception. The actual Basic retention duration and applicable
  third-party limits were not established. The explicit deletion condition is a
  reproducibility concern, not proof that all storage during an active free
  subscription is forbidden. The guide's caching suggestion does not remove
  these conditions. [T2, T5]
- **Semantics — unknown/unverified.** The US-equities guide distinguishes the
  default real-time feed's roughly 5% market-volume coverage from historical/EOD
  data, advertised as covering all US exchange volume and available on Basic
  after midnight ET following market close. This is useful feed documentation;
  it does not by itself establish regular-session-only OHLCV, auction/extended
  hours treatment, units, adjustment configuration, or historical listing
  identity for every required input. Do not apply the real-time 5% limitation
  to the differently described daily dataset. [T6]
- **Provenance — unknown/unverified.** Request parameters and retrieval time
  could be recorded by the application. Full documentation retrieval failed,
  leaving response metadata, historically scoped mapping/action inputs, and
  their snapshot retention insufficiently established in this pass. A provider
  revision identifier is not mandatory when retained responses and retrieval
  records can identify the used snapshot; that complete path was not verified.
  [T3–T5]
- **History — supported at documentation scope.** The guide advertises daily
  history from first trading date for most symbols and documents checking the
  earliest date; the US guide includes historical/EOD access on Basic. Together
  these support an advertised depth extending beyond 2021 for established US
  equities, with no one-year free cap stated on these pages. They do **not**
  demonstrate the actual 2021–2026 eligible-security panel, delisted coverage,
  gap-free sessions, or historical mappings. [T5, T6]

**Disposition:** not cleared; no deeper validation authorized by this research.

### EODHD Free

- **Access — supported.** Documentation specifies authenticated GET
  `/api/eod/{ticker}`, daily period, date bounds, and CSV/JSON output. Free
  registration provides a key; the public demo is limited to selected symbols.
  Neither route was invoked. [E2]
- **Zero cost — failed.** Free has 20 calls/day and only past-year data; the
  required historical envelope cannot be obtained through that tier. [E1]
- **Retention — unknown/unverified.** Terms expressly permit private,
  noncommercial storage/manipulation/analysis, but define the nonprofessional
  user around personal investment activities. Applicability to this project's
  Congressional research purpose and the entire retained-input contract remains
  unverified. This is not a claim of a blanket storage ban. [E6]
- **Semantics — failed.** EOD documentation says OHLC is unadjusted but volume
  is split-adjusted, conflicting with the required unadjusted OHLCV input.
  Regular-session treatment is also unverified. [E2] The source page names
  Nasdaq Cloud for US data and also CFD/market-maker EOD inputs, while its footer
  broadly disclaims exchange pricing feeds; the scope of those statements for
  a particular daily bar is unresolved. [E5]
- **Provenance — unknown/unverified.** The documented dated OHLCV response and
  ticker-qualified request support basic retrieval attribution. They do not
  establish historical listing identity/action evidence and source-specific
  input provenance sufficient for the whole retained computation. [E2, E5]
- **History — failed.** Free access to arbitrary tickers is explicitly restricted
  to the past year. Longer advertised service-wide history and selected demo
  symbols do not establish free population coverage for 2021–2026. [E1, E2]

**Disposition:** not cleared on explicit history and raw-volume incompatibilities.

### Marketstack Free

- **Access — unknown/unverified.** Pricing provides free signup and API request
  allowances, but the legacy documentation URLs returned tool errors and the
  linked APILayer documentation rendered only a shell with a login link. An
  actionable endpoint/parameter/response contract was not retrieved. This is a
  limitation of this public-document check, not evidence that the API is down.
  [M1, M2, M4, M6]
- **Zero cost — failed.** Free advertises 100 requests/month and one year of
  history; even ignoring unmeasured daily workload capacity, that history is
  insufficient for the approved minimum. [M1]
- **Retention — unknown/unverified.** The terms link leads to APILayer's legal
  hub and a generic SaaS agreement. The latter distinguishes uploaded Customer
  Data from supplied Licensed Data and has separate freeware applicability.
  Those provisions do not establish a Marketstack Free permission to preserve
  the required market-data snapshots/actions/mappings. Its hosted storage
  restrictions are not treated as a blanket ban on local response retention.
  [M3, M5]
- **Semantics — unknown/unverified.** An EOD label and advertised splits,
  dividends, currencies, and timezones do not establish regular-session-only
  OHLCV definitions, feed coverage, or adjustments. The usable endpoint
  documentation was not retrieved. [M1, M2, M4, M6]
- **Provenance — unknown/unverified.** No usable response schema or historical
  mapping/action provenance contract was obtained. This does not establish
  that provider metadata is absent. [M2, M4, M6]
- **History — failed.** Free's one-year/12-month history cannot cover full
  2021–2025 plus the current year. Paid-plan history is irrelevant to this
  zero-cost screen. [M1]

**Disposition:** not cleared on explicit historical coverage incompatibility.

## Primary-source and public-access log

All entries were checked on **2026-09-17** using public web-document retrieval.
“Readable” means the tool returned document text; it does not assert a direct
origin HTTP status or an observed data API response. Search indexing and live
page wording can differ; the opened page was preferred. No full third-party
documents or market-data responses were retained in this repository.

| ID | Primary document URL | Observation and relevant section |
|---|---|---|
| T1 | https://twelvedata.com/pricing | Readable; Basic plan and credit limits. |
| T2 | https://twelvedata.com/terms | Readable; dated Jan 1, 2026; §§2.2, 2.3(g), 12.5, 16.1–16.2. |
| T3 | https://twelvedata.com/docs | Web tool internal error on open; not evidence of origin unavailability. |
| T4 | https://api.twelvedata.com/doc/swagger/docs | Documentation URL attempt returned web tool internal error; no data endpoint called. |
| T5 | https://support.twelvedata.com/en/articles/5656039-how-to-get-historical-prices | Readable; dated Jan 12, 2026; daily-history/access sections. |
| T6 | https://support.twelvedata.com/en/articles/9935903-us-equities-market-data | Readable; historical/EOD versus real-time feed sections. |
| E1 | https://eodhd.com/pricing | Readable; Free package, 20/day, past year. |
| E2 | https://eodhd.com/financial-apis/api-for-historical-data-and-volumes | Readable; Free restriction, endpoint, response fields, adjustment behavior. |
| E3 | https://eodhd.com/terms-conditions | Web tool internal error; corrected terms link counted separately as E6. |
| E4 | https://eodhd.com/financial-apis/commercial-vs-personal-license-use/ | Readable (redirect to slashless URL); personal/commercial applicability. |
| E5 | https://eodhd.com/financial-apis/our-data-sources-and-data-partners | Readable; US source attribution, other EOD inputs, footer qualification. |
| E6 | https://eodhd.com/financial-apis/terms-conditions | Readable; Personal and Commercial Use of Information. |
| M1 | https://marketstack.com/product | Redirect to https://marketstack.com/pricing; readable Free plan and FAQ. |
| M2 | https://marketstack.com/documentation | Web tool internal error. |
| M3 | https://marketstack.com/terms | Redirect to https://www.ideracorp.com/legal/APILayer; readable legal hub. |
| M4 | https://docs.apilayer.com/marketstack/docs/api-documentation?utm_medium=Referral&utm_source=MarketstackHomePage | Official pricing documentation link; shell only, no endpoint content. |
| M5 | https://www.ideracorp.com/~/media/IderaInc/Files/APILayer/Apilayer%20Master%20Software%20as%20a%20Service%20Subscription%20Agreement%20SaaS%20082523ns%20FORM | Readable six-page PDF; version 082523ns; introduction, §§1(c/e), 2(c), 6(f). |
| M6 | https://marketstack.com/documentation_v2 | Web tool internal error. |

## Handoff and limits

Return this scoped blocker to the Wayfinder map and the existing [market-data
route decision](https://github.com/AviSharma01/signal-workspace/issues/22).
No additional round or operational trial follows automatically. Unsupported
requirements remain unsupported; the contract and zero-cost constraint were not
weakened. An eventual human decision may address the blocker, but this report
does not make that decision.

No numerical correctness, retained-input recomputation, real panel coverage,
historical identity, independent fixtures, uptime, rate-limit behavior, or
backfill/catch-up workload was tested. No missing values were treated as zeros.
The stopping rule is completion of this fixed prerequisite screen, not exhaustion
of possible sources or resolution of every provider ambiguity.

The coordinating agent reviewed the matrix against the approved contract and re-opened already inventoried EODHD/Marketstack pricing, Twelve Data terms/history/US-equity guidance, and EODHD EOD documentation. No new candidate or source page was added. The research subagent reached its usage limit after writing the draft; coordination completed review and publication.
