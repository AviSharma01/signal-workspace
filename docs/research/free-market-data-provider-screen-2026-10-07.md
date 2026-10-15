# Free market-data route screen

Research observation date: **2026-10-07**. Documentation research only; no provider
approval, authenticated API experiment, production integration, or code change.
The unchanged acceptance boundary is [#31](https://github.com/AviSharma01/signal-workspace/issues/31)
and [market-data conformance](../market-data-conformance.md), under approved
[#26](https://github.com/AviSharma01/signal-workspace/issues/26). Required history
is complete **2021–2025 plus 2026 through evaluation**.

**No free route is currently defensibly cleared for production.** Free access,
long advertised history, and a local download button do not together establish
retention rights, raw regular-session OHLCV, complete action coverage, historical
identity, or retained-input replay. Composite inputs are acceptable only when
each component and their joins satisfy those requirements.

## Contract and comparison

#31's completed provider-neutral harness has 28 gates; its synthetic fixtures do
not approve any real provider. Completion is recorded at commit
`5688e13ae040e84be526de99a9bba33e938e1394`; this research inspected checkout
`8b6002baa053d8d79e29cee17136b7f1322468bd`. Production approval needs independent
evidence and explicit human approval. The approved
[V2 specification](../specs/signal-v2.md) requires SPY-compatible sessions,
unadjusted daily regular-session OHLCV and separate action evidence. A noncash
action, merger/spinoff or delisting can make an outcome unavailable under the
current methodology; the requirement is to recognize the lifecycle boundary,
not invent a terminal return. Missing market evidence must not erase Events.

Legend: **P = PASS; F = FAIL; U = UNKNOWN; E = EMPIRICAL TEST REQUIRED**.
These are screening classifications, not #31 approval. E means a plausible
documented capability still needs measurement; it does not resolve legal U.
Only the first two routes merit further clarification. The other two illustrate
why attractive free offerings cannot currently be shortlisted.

| Hard gate | Stooq + supplements | Twelve Data Basic + supplements | Alpaca Basic daily | Finnhub Free |
|---|---|---|---|---|
| Local raw persistence | U: local downloads intended; archival grant unclear | U: tier-dependent storage/cache terms | U | U |
| Retained versions and derived outputs | U | U: cache/display/termination limits | U | U: termination deletion; sharing restricted |
| Personal-use category | P for private noncommercial use | P for noncommercial category; display U | U for complete data-license scope | P only if eligible personal user |
| Five complete years + current | E for established names; delisted U | E for established names; delisted U | E: advertised since 2016; delisted U | U: required free entitlement unestablished |
| Raw regular-session OHLCV | E after session/feed definitions clarified (U) | U | **F: extended-hours volume** | U |
| Original dividends/splits and other actions | U: nominal values recalculated; supplements incomplete | U: free entitlement/completeness | U | U |
| Historical identity, reuse, listings, delistings | U | U | U | U |
| Historical sessions, DST, early closes, exact SPY join | E with validated calendars; source timestamps U | U/E with validated calendars | U/E; daily-volume failure remains | U |
| Limits, daily catch-up, revisions and provenance | U/E | U/E: 8 credits/min, 800/day | U/E: advertised 200/min; direct route rejected | U/E: 60/min; entitlement U |

No route has passed the complete legal gate. None therefore reaches a production
data experiment or approval decision in this exercise.

## Provider findings

**Finnhub — not cleared; retention gate unresolved with an explicit deletion
obligation.** Its terms require deleting data when the subscription ends, restrict
plans to personal use, and require permission to share data or derived results.
Personal research is consistent with the personal-use category if the user is
not disqualified by professional/business status; sharing Signal results is a
separate restriction. These provisions do not establish permission to retain
historical raw versions and derived outputs durably for replay. Do not infer a
retention license from endpoint accessibility. The free candle entitlement and
raw/action/session definitions were not established by the readable primary
documents in this bounded pass; those technical gates remain UNKNOWN, rather
than being promoted from secondary descriptions to documented FAIL.
[Official terms](https://finnhub.io/terms-of-service),
[official pricing](https://finnhub.io/pricing),
[candle documentation](https://finnhub.io/docs/api/stock-candles).

**Tiingo Starter — hard legal FAIL; reject.** Current terms dated October 6,
2026 prohibit Starter/trial users from writing, saving, archiving, or backing up
Tiingo data or derived products in persistent storage, including local files,
databases and logs. Only transient session/job processing is allowed. This
directly conflicts with #31 retained snapshots and deterministic reproduction,
regardless of the advertised long history and usable free quotas. A composite
cannot repair the prohibited retention of its price component.
[Current terms §1.6(a)](https://app.tiingo.com/tos/),
[Starter pricing](https://www.tiingo.com/pricing).

**Alpaca Basic daily bars — technical FAIL for the direct daily-bar route.**
The free plan advertises stocks/ETFs since 2016 and 200 historical calls/minute.
Its FAQ permits historical SIP queries with an end at least 15 minutes old,
while another support page describes free data as IEX; actual entitlement needs
an account experiment. More importantly, daily aggregate volume includes
extended-hours qualifying trades. It is not the required raw regular-session
OHLCV. Adding corporate actions or a calendar cannot remove those trades from
an already aggregated volume. Building separate regular-session bars from
intraday inputs would require newly approved scope and meaningful validation;
it is not a cleared route under the present daily-input exercise. Raw and
adjustment options, symbol `asof`, and an actions endpoint are useful features,
but do not cure the direct-route failure or certify ticker reuse and local
archive rights.
[Plan](https://docs.alpaca.markets/us/v1.1/docs/about-market-data-api),
[FAQ](https://docs.alpaca.markets/us/docs/market-data-faq),
[feed support](https://alpaca.markets/support/data-provider-alpaca),
[bars](https://docs.alpaca.markets/us/reference/stockbars),
[terms](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf).

**Twelve Data Basic composite — unresolved research lead, not an adoption
recommendation.** Basic advertises $0, 800 daily credits and internal non-display
use. Official history guidance advertises daily history from first trading date
for most symbols; the US-equity guide separates limited real-time coverage from
historical/EOD full-market-volume coverage. This supports advertised depth for
established names, not complete delisted history or regular-session-only bars.
Terms permit tier-dependent internal storage, but defer caching duration and
retention to documentation/subscription/third-party restrictions and require
data deletion on termination. Sufficient active-subscription raw-version
retention and permission for Signal's displayed outputs remain UNKNOWN.
Unadjusted OHLCV, independently attributable actions, delisted mappings and
revision behavior require further primary-document clarification before a
probe could certify anything.
[Pricing](https://twelvedata.com/pricing),
[terms §§2.2–2.3,12.5,16](https://twelvedata.com/terms),
[history guide](https://support.twelvedata.com/en/articles/5656039-how-to-get-historical-prices),
[US-equity guide](https://support.twelvedata.com/en/articles/9935903-us-equities-market-data).

**Stooq composite — unresolved research lead.** The official bulk download page
offers US daily files, local disk instructions and personal-only use. AAPL's
history UI starts in 1984 and exposes adjustment skip controls. This means
adjusted-only incompatibility is not established: whether those controls deliver
genuinely unadjusted full-history OHLCV is EMPIRICAL TEST REQUIRED, following
provider clarification of feed/session/volume definitions. The separate
operations table recalculates nominal action values through later operations;
it must not be treated as original cash-distribution evidence. Explicit rights
to retain old snapshots and derived outputs, delisted coverage, ticker reuse,
revision detection and reliable unattended daily acquisition remain UNKNOWN.
[Bulk downloads](https://stooq.com/db/h/),
[terms](https://stooq.com/terms.html),
[AAPL history](https://stooq.com/q/d/?s=aapl.us),
[AAPL operations](https://stooq.com/q/m/?s=aapl.us).

## Additional explicit rejects

Massive Basic advertises only two years of price history; Marketstack Free one
year. EODHD Free likewise limits history to the past year. These fail the
unchanged history contract,
even when other sources contribute actions and identities.
[Massive pricing](https://massive.com/pricing),
[Marketstack pricing](https://marketstack.com/pricing),
[EODHD pricing](https://eodhd.com/pricing).
Alpha Vantage's daily endpoint makes only the most recent 100 observations
available through free compact output; full daily history is premium. This is a
history FAIL; weekly/monthly endpoints are not substitutes for daily inputs.
[Official API documentation](https://www.alphavantage.co/documentation/).

Yahoo through yfinance is not an established licensing route: the project's own
documentation distinguishes its software license from Yahoo's data rights and
directs users to Yahoo's terms. Durable archive rights and a supported historical
identity contract remain U, not a demonstrated legal FAIL.
[yfinance documentation](https://ranaroussi.github.io/yfinance/).

## Can authoritative free supplements close the gaps?

**OpenFIGI: useful identity component, not a historical security master.** Its
FAQ explicitly allows storing/reusing metadata; FIGI identifiers are open and
not reused. That component's licensing is P. However, allocation rules say an
old ticker ceases to be associated with its FIGI after a ticker change. A current
lookup does not provide the dated symbol intervals or knowledge vintages #31
requires. Complete historical identity coverage is U.
[FAQ](https://www.openfigi.com/about/faq),
[allocation rules](https://www.openfigi.com/assets/local/figi-allocation-rules.pdf).

**SEC and exchange notices: authoritative dated evidence with incomplete
normalized coverage.** SEC provides free EDGAR archives from 1994, bulk APIs and
a 10 requests/second ceiling. Current ticker/CIK/exchange files are not guaranteed
complete historical security mappings; a CIK identifies a filer, not necessarily
a particular share class. Filings can substantiate a rename, merger, split or
delisting, but an aggregate XBRL dividend fact is not a complete ex-date/action
ledger. Archive completeness, extraction semantics and applicable content rights
must be assessed rather than assuming all filing contents are public domain.
[EDGAR access](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data),
[APIs](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).

Nasdaq explicitly permits unrestricted use of certain **Nasdaq Events Data**,
including Security Status Updates and Ex-Date information: P for that named
metadata subset's licensing. Status updates expose dated additions, suspensions
and symbol/name changes. However, the post-T+1 Ex-Date feed publishes exceptions
where ex-date differs from record date; it is not a full dividend ledger. The
comprehensive historical Daily List is a subscription product. FINRA's free OTC
Daily List/archive can provide some terminal/OTC transitions, but is not a full
listed-US-equity action source, and its applicable archive rights remain U.
[Nasdaq rights notice](https://nasdaqtrader.com/trader.aspx?id=symbollookup),
[status updates](https://www.nasdaqtrader.com/Trader.aspx?id=nasdaq-security-status-updates),
[Ex-Date](https://www.nasdaqtrader.com/Trader.aspx?id=nasdaq-ex-date),
[Daily List](https://classic.nasdaqtrader.com/Trader.aspx?id=DailyListPD),
[FINRA archive](https://otce-dr.finra.org/otce/DailyList/archives).

**Calendars: feasible free component, still requires validation.** Versioned
`exchange_calendars` software is Apache-2.0 licensed and supplies historical
schedules/UTC timestamps. Independently compare its relevant schedules against
official exchange notices, including exceptional closures, early closes and DST.
NYSE's current calendar page alone does not verify every session in 2021–2026.
A correct calendar cannot establish a vendor's bar boundaries or remove
extended-hours volume. Exact security/SPY compatibility remains E.
[exchange_calendars](https://github.com/gerrymanoim/exchange_calendars),
[NYSE hours/calendars](https://www.nyse.com/trade/hours-calendars).

**Inference:** Stooq raw exports plus these components is the strongest free
feasibility lead, but the reviewed evidence does not close original action,
historical identity, delisted-price or retention gaps. Twelve Data plus the same
supplements is a second clarification lead. A composite does not eliminate
these missing components or establish compatible units, venues and vintages.
Deterministic source selection and independent join validation are required;
do not average providers or silently stitch observations.

## Required next decision

Do not write a production adapter yet. The smallest next action is a narrowly
scoped written clarification from **Stooq** about **free local raw-response and
historical-version archival rights, derived-output retention, and unadjusted
regular-session OHLCV definitions**. A provider response is needed for legal
ambiguity; an API experiment cannot grant rights. Only after those gates clear
should a small independently anchored #31 panel test SPY alignment, early closes,
splits/dividends, a rename, ticker reuse, a delisting, repeated retrieval,
revision preservation and offline replay. Workload feasibility remains
EMPIRICAL TEST REQUIRED. No data or messages to providers were sent by this
exercise.

The first experiment, if permissions/definitions clear, should compare retained
Stooq exports against independently sourced AAPL/SPY dividend evidence, a split,
FB→META, a verified ticker-reuse case and a delisted security. Check original
nominal cash amounts, split ratios, bar units/volume and every relevant session
boundary rather than comparing two adjusted series. Measure request counts,
elapsed time, storage and memory for a bounded backfill and catch-up.

For revisions, repeated overlapping retrieval plus content hashes may detect
changed observations even without native vendor revision IDs; preserve both
responses with retrieval times and provenance and demonstrate offline replay.
Whether that is practical within free limits is E, and the refresh policy remains
unapproved. The contract requires retaining earlier versions actually observed,
not reconstructing every version a vendor ever published. Conversely, a newly
downloaded corrected historical series cannot establish a past knowledge vintage
or be silently used before its declared availability boundary.

Provider capabilities above are documented facts where an official source is
cited; the explicitly labeled composite conclusion is inference. UI observations
of Stooq's adjustment controls and history range are not numerical verification.
No authenticated API or downloaded-series experiment was performed. Legal U
requires authoritative licensing clarification, not a successful API response.
