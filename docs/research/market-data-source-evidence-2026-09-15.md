# Market-data coverage and temporal correctness evidence

Research date: 2026-09-15. Status: evidence, not an approved provider or methodology.

Resolves [Establish market data coverage and temporal correctness evidence](https://github.com/AviSharma01/signal-workspace/issues/9) under the [Signal V2 architecture and research methodology map](https://github.com/AviSharma01/signal-workspace/issues/1).

## Scope and evidence standard

The [approved operating constraints](https://github.com/AviSharma01/signal-workspace/issues/2#issuecomment-5677296093) target individual publicly traded equities, five complete calendar years plus the current year, preferably 2012 onward, daily local operation, and a deterministic core independent of paid data. In September 2026, the minimum period starts in January 2021. A rolling five-year entitlement does not establish that minimum.

This bounded review covers the incumbent yfinance path, Alpaca, Massive, and Alpha Vantage, with FRED, exchange calendars, and CRSP as reference candidates. It is not a census of vendors. All external facts below come from first-party documentation read on the research date. No authenticated market-data queries, bulk downloads, account creation, purchases, or numerical comparisons were performed. Documentation reachability does not verify API entitlement, complete coverage, freshness, or reliability. Unknown means not established by this review, not that the capability cannot exist.

## Coverage and access comparison

| Candidate | Documented capability and access | Fit and unresolved evidence |
|---|---|---|
| Yahoo through yfinance | The library exposes daily and intraday OHLC, volume, dividend and split retrieval. Its download documentation supports long daily periods but limits intraday requests to recent history. The project is unaffiliated with Yahoo and directs users to Yahoo's data-use terms; its open-source license is not a data license. [Library documentation](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html), [project notice](https://github.com/ranaroussi/yfinance). | An existing integration is useful for bounded comparisons, but neither a complete historical equity universe nor delisted-security coverage, service reliability, or historical data vintages is established. A `max` period is not a completeness guarantee. |
| Alpaca | Basic advertises free US stocks/ETF data since 2016, 200 historical calls/minute, IEX-only real-time coverage and a recent-15-minute restriction. Algo Trader Plus advertises $99/month. Authentication is required for equity data. [Plan documentation](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api). | The advertised start could cover 2021 onward, but not the full preferred 2012 onward period. Per-symbol completeness, account eligibility, and access from this user's account remain untested. |
| Massive | Stocks Basic advertises $0, five calls/minute and two years of history. [Pricing](https://massive.com/pricing). Aggregate endpoint entitlements list Starter $29/month with five years, Developer $79/month with ten years, and Advanced $199/month with history from September 2003. Basic is end-of-day; Starter/Developer are 15-minute delayed. [Aggregate contract](https://massive.com/docs/rest/stocks/aggregates/custom-bars). | Free aggregate history is insufficient. Five years does not establish five complete years plus current year. Longer paid access needs separate approval and does not itself prove coverage. The product advertises retained delisted histories, a capability claim still requiring samples. [Stock product](https://www.massive.com/stocks). |
| Alpha Vantage | Daily raw OHLCV and Daily Adjusted advertise 25+ years; Daily Adjusted includes adjusted close, dividends and splits and is marked Premium. Default compact responses contain 100 points; full is a separate request. Listing Status supports active/delisted US stocks and ETFs at dates after 2010-01-01. [API documentation](https://www.alphavantage.co/documentation/). Free service advertises 25 calls/day. [Support](https://www.alphavantage.co/support/). | Advertised history length does not establish free full-history entitlement or price coverage for every delisted symbol. The free quota constrains backfill and daily breadth; workload is unmeasured. Premium costs and entitlement for the required endpoint combination remain unverified. |

### Alpaca documentation conflict

The [Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq) explicitly permits historical SIP queries without a subscription when `end` is at least 15 minutes old; latest SIP endpoints require a subscription. However, the [historical stock overview](https://docs.alpaca.markets/us/v1.1/docs/historical-stock-data-1) describes IEX as the only subscription-free feed. This is an unresolved documentation inconsistency, not proof that free consolidated history is unavailable or verified. A bounded authenticated request with explicit `feed=sip` and dates would resolve practical entitlement. Do not silently substitute IEX: it represents one exchange, not consolidated market volume. The FAQ also limits OTC access to a special broker-partner subscription; delisted securities continuing OTC therefore need explicit treatment.

## Adjustments, identities, and time

### Alpaca

The [historical bars API](https://docs.alpaca.markets/us/reference/stockbars) defaults to raw bars and offers split, cash-dividend, spin-off and combined adjustments. Its `asof` date identifies the entity associated with a ticker and maps previous names; it defaults to the current day. It does **not** document replay of the database as it was known on that date. Requests have inclusive start/end bounds and pagination across the total result set. These details matter when comparing providers or handling ticker reuse.

The [corporate-actions API](https://docs.alpaca.markets/us/reference/corporateactions-1) includes splits, dividends, mergers, name changes and other actions. It explicitly gives no guarantee of creation time and warns of provider/processing delays. Its completeness filter can exclude early incomplete records. An action's economic date therefore cannot establish when Alpaca first supplied it.

The [streaming contract](https://docs.alpaca.markets/us/docs/real-time-stock-pricing-data) distinguishes initial minute bars, updated bars after late trades, evolving daily bars, trade corrections and cancellations. An example updates a previous minute's bar after its first emission. Bar time, observation time and finality are different facts. This is documented behavior, not a revision measured in Signal.

### Massive

The [aggregate API](https://massive.com/docs/rest/stocks/aggregates/custom-bars) uses eligible trades, covers extended as well as regular sessions, and may omit intervals without qualifying trades. Its `t` is the aggregate-window start in Unix milliseconds; `adjusted` means split adjustment. That is not publication time or a total-return promise.

The [ticker API](https://massive.com/docs/rest/stocks/tickers/all-tickers) has historical `date` and active/inactive filters, FIGI fields, a delisting date and update metadata. Default active-only queries can omit historical securities. These fields are useful evidence for security resolution; they do not prove a complete lineage through all reorganizations or historical knowledge-vintage replay.

The current [dividend endpoint](https://massive.com/docs/rest/stocks/corporate-actions/dividends) separates original cash amount, declaration/ex/record/pay dates and adjustment fields. It lists daily updates, two-year Basic history and all-history paid access beginning January 2000. The [February 2026 endpoint announcement](https://www.massive.com/blog/new-splits-and-dividends-endpoints) describes separate split-adjusted cash amounts and factors while native dividend adjustment of aggregates remains future work. Do not equate every field called adjusted. Historical retention is endpoint-specific.

### yfinance and Alpha Vantage

The [yfinance download contract](https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html) defaults to automatic OHLC adjustment, has separate actions/repair controls, an exclusive end date, and interval-dependent timezone handling. These are current library documentation, not verification of the installed version or `Ticker.history` defaults. Preserve the chosen method, library version, arguments and original response when evaluating it.

Alpha Vantage's [documented listing-date query](https://www.alphavantage.co/documentation/) describes historical membership, not when each record became known. Adjusted close is distinct from raw OHLCV. Neither that page nor the yfinance material inspected establishes a complete archive of old revisions or first-availability timestamps. Neither establishes terminal delisting returns merely by exposing prices or listing status.

## Benchmarks, calendars, and independent references

- **Benchmark series:** Alpaca explicitly includes ETFs in its coverage. ETF market prices, fund NAV and an index's price/total-return series are distinct possible inputs, not interchangeable benchmarks. [FRED SP500](https://fred.stlouisfed.org/series/SP500) documents ten years of daily closing index history, excludes dividends, identifies S&P as the source, and carries reproduction restrictions. It is a possible price-index reference, not individual-stock OHLCV or a selected benchmark. Its update time does not certify first availability of every historical observation.
- **Exchange calendars:** [NYSE hours and calendars](https://www.nyse.com/trade/hours-calendars) supply official holidays, early closes and session definitions in Eastern Time. [Alpaca's broker calendar documentation](https://docs.alpaca.markets/us/v1.1/reference/querymarketcalendar-1) describes market dates and opening/closing times from 1970–2029, including early closures. Broker-endpoint availability does not establish access through a regular data account. Validate the chosen calendar interface and historical exceptions; a weekday-only gate is insufficient.
- **Security lifecycle reference:** [CRSP's research products](https://www.crsp.org/research/) describe permanent PERMNO identifiers and institution-oriented subscriptions. Its [data definitions](https://www.crsp.org/crsp_pdf/crsp-us-stock-indexes-databases-data-descriptions-guide-crspaccess/) describe delisting returns and missing-value cases. These provide an independent semantic reference and a possible licensed numerical comparison, not a free operating dependency. Access and price were not established.
- **Independence limit:** Two APIs may share exchange inputs. Agreement is a useful cross-check, not independent proof of correctness. For a bounded fixture, use exchange calendar evidence for session boundaries and issuer action announcements for split/dividend facts, then compare like-for-like raw/adjusted series. No such numeric fixture has been run in this research.

## Access, retention, and reproducibility limits

No candidate is certified here for unrestricted redistribution, indefinite local retention after cancellation, or storing all historical response vintages. Advertised history is an access window, not a retention license. Massive's listed plans are individual-use plans; yfinance explicitly separates software licensing from Yahoo data rights; FRED's series notes restrict reproduction. Account-specific agreements and permitted local retention must be checked before acquisition is adopted. This report does not grant rights or recommend buying access.

Across the inspected endpoints, historical observation dates and symbol-effective dates do not establish historical knowledge. The evidence supports keeping three questions separate in the downstream contract: what happened economically, when a source supplied it, and which version was used by a computation. Nothing here approves an availability-time surrogate, revision policy or treatment of future corporate actions.

## Bounded local inspection

At checkout HEAD `22f4ebbc960da31a5cd6c411c79268e4af02e388`, [the price job](https://github.com/AviSharma01/signal-workspace/blob/22f4ebbc960da31a5cd6c411c79268e4af02e388/server/jobs/prices.py) requests `Ticker.history(period="1d", interval="5m")` for seeded tickers, gates on weekdays and wall-clock hours, and inserts OHLCV with `INSERT OR IGNORE`. [Requirements](https://github.com/AviSharma01/signal-workspace/blob/22f4ebbc960da31a5cd6c411c79268e4af02e388/server/requirements.txt) do not pin yfinance. This is source inspection only: no runtime, stored-data quality, historical completeness or correction behavior was tested. No application code was changed.

## Handoff

The evidence question is answered at documentation level: plausible acquisition routes exist, but no inspected candidate is verified to satisfy the full zero-cost historical, security-lifecycle and point-in-time contract. Missing entitlement/coverage evidence must remain explicit.

[Define the minimum reliable market data contract](https://github.com/AviSharma01/signal-workspace/issues/10) already owns the resulting decisions and validation requirements, after event/as-of semantics are settled. Useful bounded checks for that discussion are:

1. Verify account entitlement and first/last available bars on a small, declared panel spanning the minimum period, one symbol rename, one delisting and one split/dividend. Measure missingness and pagination rather than infer completeness from one successful ticker.
2. Compare a small like-for-like sample across independently implemented sources, including an early-close session and correction/adjustment cases. State feed, timezone, session, adjustment and rounding conventions before comparison.
3. Establish permitted retention, update/finality behavior, replay requirements and what can be known at each As-Of Boundary. Price-bar time and ticker `asof` must not substitute for evidence availability.
4. Measure request counts, catch-up duration and local storage for the required universe before choosing orchestration or Python/q boundaries.

These are proposed validation inputs, not approved tests or newly created tasks. No provider, benchmark, return formula, event window, database, language boundary or fallback policy is selected. No additional map ticket is needed: the existing contract decision and event-study fog already own the exposed questions.
