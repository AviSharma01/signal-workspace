# Yahoo prerequisite evidence

Bounded research for [Validate Yahoo access, retention, daily-bar semantics, and provenance prerequisites](https://github.com/AviSharma01/signal-workspace/issues/17), checked 2026-09-17. Evidence only; no provider adoption or legal determination.

## Result

**The four prerequisites are not demonstrated. Stop before a larger Yahoo coverage trial.** Each gate is unsupported under this bounded check; none is recorded as a demonstrated technical impossibility. The applicable acquisition/retention permission is unresolved, daily-bar semantics remain incomplete, and no response-level reproduction was tested.

| Gate | Status | Evidence and limit |
|---|---|---|
| Practical zero-cost access | Unsupported | A client implementation exposes a chart route, but no authorized operational path was demonstrated. No market-data request was made. This does not establish provider outage or technical failure. |
| Local retention and reproduction permission | Unsupported | Inspected Yahoo terms require prior permission for automated collection. No applicable grant covering this workflow and retained input versions was established. Client licensing is not data permission. |
| Daily regular-session/venue semantics | Unsupported | Client request controls and general provider attribution do not establish all daily OHLCV session and venue definitions required by the contract. |
| Reproducible source/provenance | Unsupported | Client code exposes request and metadata handling, but no permitted raw-response snapshot or independently sufficient field provenance was demonstrated. |

These statuses describe evidence sufficiency for Signal's acceptance gates, not a claim that Yahoo can never satisfy them. The already approved source-strategy rule requires stopping when a prerequisite remains unsupported.

## Scope and execution

The [probe scope](https://github.com/AviSharma01/signal-workspace/issues/17#issuecomment-5709527728) was recorded before any market-data probe: first-party terms/help and client code; at most one unauthenticated AAPL daily-chart request for June 3–7, 2024, with extended-hours inclusion disabled, conditional on establishing applicable access/retention permission. That condition was not met, so **zero market-data probes** ran. No accounts, purchases, cookies, access workarounds, polling, backfill, symbol sweep, ingestion or application changes occurred.

A research subagent declared the scope but hit a usage limit before delivering findings; the coordinating agent completed this documentation review. No sample-based claim relies on unreturned subagent work.

## Permission evidence and retrieval limits

The [Yahoo India-locale general terms](https://legal.yahoo.com/in/en/yahoo/terms/otos/index.html), section 2.4.9, require express prior permission for automated collection. The workspace timezone motivated inspecting this locale; it does not establish the user's legal residence or definitive contractual jurisdiction. The review found no workflow-specific authorization for recurring automated acquisition and preserved historical input versions. This is insufficient evidence of permission, rather than a categorical interpretation that all personal retention is prohibited.

Direct browser opening of that page returned status 999; the search tool returned indexed primary-source text including the relevant section. Direct opening of the [API additional-terms URL](https://legal.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.html) also returned 999, so its contents and applicability were not established. The indexed [Developer Network guidelines](https://legal.yahoo.com/us/en/yahoo/guidelines/ydn/index.html) discuss storage of user data; that language is not evidence that a particular retention rule applies to market bars. Do not substitute it for a Finance-specific grant.

The [yfinance project](https://github.com/ranaroussi/yfinance) describes itself as an independent client and directs users to Yahoo's terms, describing the API as intended for personal use. A client author's characterization does not establish Yahoo's permission for this workflow. Software licensing and data rights remain separate.

## Semantics and provenance evidence

Yahoo's indexed [exchange/provider help](https://help.yahoo.com/kb/SLN2310.html) attributes US-equity/global-index historical data and daily updates to Commodity Systems, Inc. General attribution does not settle the exact contributing venues, consolidated-volume meaning or regular-session OHLC construction of a particular chart response. Direct opening returned 429. The [historical-download help](https://help.yahoo.com/kb/sln2311.html) was indexed as describing price/dividend/split history; direct opening also returned 429. Neither establishes the intended zero-cost automated retention path.

Inspected [yfinance history implementation](https://raw.githubusercontent.com/ranaroussi/yfinance/main/yfinance/scrapers/history.py), accessed on the stated date. Repository main resolved during inspection to `3d9d2f0cacb662bff689874cd6113bae3a30a885`; [commit reference](https://github.com/ranaroussi/yfinance/tree/3d9d2f0cacb662bff689874cd6113bae3a30a885). The viewed raw URL was mutable main, not a retained byte-for-byte snapshot of that commit.

The implementation defaults to daily intervals, pre/post exclusion and automatic OHLC adjustment; it passes interval and includePrePost to the chart endpoint and handles response metadata including exchange timezone and currency. It parses, adjusts and cleans data, so its returned table is not an untouched response. Requesting no extended hours does not independently certify daily-bar semantics. Reproduction would require preserving actual response bytes, parameters/retrieval time, metadata, and transformation version/settings under demonstrated retention permission. No such sample was captured here.

## Handoff

Return the evidence to [Assess Yahoo prerequisite evidence and choose the next market-data validation route](https://github.com/AviSharma01/signal-workspace/issues/18). Under the approved gate, a broad Yahoo trial is not justified. Alternative-source discovery should seek explicit zero-cost acquisition and retention rights, authoritative daily-session/venue definitions and reproducible raw inputs before broad coverage work. No alternative provider is selected by this report.

Five-year/current-year history, delisted identities, corporate actions, revision behavior, missingness, exchange-calendar compatibility, catch-up and operational reliability remain untested. Documentation access errors are observations about this tool/check, not evidence of market endpoint failure. No existing contract is relaxed.
