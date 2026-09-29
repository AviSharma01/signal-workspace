# Final bounded Raw Consensus evidence sample

Observed **2026-09-29 UTC**. Research for [Establish one final bounded Raw Consensus evidence sample](https://github.com/AviSharma01/signal-workspace/issues/25), under the [frozen pre-acquisition plan](https://github.com/AviSharma01/signal-workspace/issues/25#issuecomment-5895359257). This is evidence for the route decision, not a methodology change, approved window, source-readiness certification, or resolution of a downstream Consensus ticket.

## Verdict and handoff

**Unsupported within the frozen final effort.** The independent archive inventory did not contain a usable sequence of preserved official House annual-index representations for the frozen 2025-09-01 through 2025-09-14 period. The last distinct preserved representation before the period was captured 2025-07-06 22:04:25 UTC; the next was captured 2026-02-06 22:50:39 UTC. That seven-month observation interval cannot establish that any `P`-type DocID first appeared within the 14-day population, much less provide the approved publication precision for an eligible target and its contextual cutoff.

The frozen stop rule therefore fired after three archive/index request attempts. No target or peer filing artifact was requested, no Event was admitted, and no Raw Consensus or Other Reporting Members value was computed. The result is **unavailable**, not an observed zero. The ticket's success criterion was not met.

This finding does not establish that no House disclosures were published in the period, that the official index lacked entries, that Raw Consensus is conceptually invalid, or that another future evidence source could never support it. It establishes only that the single authorized final plan could not produce a defensible bounded population without changing the period, source inventory, or temporal semantics. Per the authorization, it supports returning to [Decide the Raw Consensus route after unsupported computability evidence](https://github.com/AviSharma01/signal-workspace/issues/24); it authorizes no third search.

## Frozen scope

- House only; official filing year 2025.
- Source-local period `[2025-09-01 00:00 EDT, 2025-09-15 00:00 EDT)`, with target candidates restricted to September 8–14.
- A seven-calendar-day diagnostic lookback, solely to test parameterized computability under the approved start-inclusive, target-open-exclusive window.
- Candidate population defined by `P`-type DocIDs whose supported first-appearance interval in preserved official-index representations was wholly within the frozen period.
- First three target candidates ordered by appearance-interval upper bound and numeric DocID; no fourth-candidate replacement.
- Every other candidate in the bounded population had to be retrieved as the exhaustive peer-artifact scope, stopping rather than sampling if it exceeded 40.

The plan relied on the [official House 2025 annual index URL](https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025FD.ZIP) as the official index identity and on Internet Archive CDX/Wayback observations only as separately attributed evidence that a representation of that official URL had been observed. An archive capture was never eligible to replace official filing content or convert House `FilingDate`, transaction date, signature date, current retrieval, or archive time into an unsupported original-publication date.

## Request log and provenance

All three request attempts were to the independent Internet Archive CDX service. Failed attempts count. HTTP `Date` values below are response metadata, not disclosure publication evidence.

| # | UTC response time | Request | Result | Retained temporary response evidence |
|---:|---|---|---|---|
| 1 | 2026-09-29 17:37:05 | Exact official-index URL, frozen-period vicinity, but with `filter=collapse:digest` | HTTP 400. The response reported `field 'collapse' is not found`; this was a counted query-syntax failure. | Headers: 608 bytes, SHA-256 `4d98751b9da1b83c5332d8a9f368e29c6186976020c4cc9935819f91ce95011a`; zero response-body bytes retained. |
| 2 | 2026-09-29 17:37:47 | [Exact URL, 2025-08-25 through 2025-09-20, status 200, distinct digests](https://web.archive.org/cdx/search/cdx?url=disclosures-clerk.house.gov%2Fpublic_disc%2Ffinancial-pdfs%2F2025FD.ZIP&from=20250825&to=20250920&output=json&filter=statuscode%3A200&collapse=digest&fl=timestamp%2Coriginal%2Cstatuscode%2Cdigest%2Clength%2Cmimetype) | HTTP 200 with JSON `[]`: no matching capture in the query's bracketing interval. | Body: 3 bytes, SHA-256 `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`; headers: 607 bytes, SHA-256 `fa4057d64d2024d6525bd845d03bb6ee0e13e61d84e84f9414a12dfae500d9f3`. |
| 3 | 2026-09-29 17:39:14 | [Exact URL, all dates, status 200, distinct digests](https://web.archive.org/cdx/search/cdx?url=disclosures-clerk.house.gov%2Fpublic_disc%2Ffinancial-pdfs%2F2025FD.ZIP&output=json&filter=statuscode%3A200&collapse=digest&fl=timestamp%2Coriginal%2Cstatuscode%2Cdigest%2Clength%2Cmimetype) | HTTP 200 with 11 distinct-digest capture rows. Captures run from 2025-01-09 through 2026-09-29, but none falls from 2025-07-07 through 2026-02-05. | Body: 2,004 bytes, SHA-256 `d464941667a16e100c082008b879c1874161a960f068ef82415ab941501b7e7f`; headers: 606 bytes, SHA-256 `3d9764331208c5b2ad753fcd480072945e40d940b5d244fc02af16d63380d54c`. |

The all-date response identified the archived original as `https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025FD.zip`; URL-case normalization does not change the evidentiary limit. The decisive adjacent distinct-digest rows were:

| Capture timestamp (UTC) | CDX digest | CDX length | Reported MIME type |
|---|---|---:|---|
| 2025-07-06 22:04:25 | `ZG5VS4SHEIWSLFJUZQ3X6KIRZHCTQTKD` | 28,039 | `application/x-zip-compressed` |
| 2026-02-06 22:50:39 | `QZVWJPUWCXAL5L54ABQORPG2YZUDVGYG` | 73,607 | `application/x-zip-compressed` |

These are CDX metadata about independent captures, not hashes or publication metadata supplied by the House. No archived ZIP body was requested because no pair could yield an appearance interval wholly inside the frozen period. Fetching and diffing the July and February bodies could only assign a newly observed DocID to the broad `(2025-07-06 22:04:25, 2026-02-06 22:50:39]` interval; it could not satisfy the plan's 14-day population or the approved publication boundary.

### Exact allocation usage

| Allocation | Used | Frozen maximum |
|---|---:|---:|
| Independent archive / official index attempts | 3 | 12 |
| Official disclosure-artifact attempts | 0 | 43 |
| Official documentation / metadata attempts | 0 | 8 |
| Contingency attempts | 0 | 5 |
| **All external evidence request attempts** | **3** | **68** |
| Target filings | 0 selected | 3 |
| Peer filing artifacts | 0 | 40 |
| Filing years / chambers / population days | 1 / 1 / 14 | 1 / 1 / 14 |
| Findings reports | 1 | 1 |

The frozen plan was posted at 2026-09-29 17:33:46 UTC. The decisive third response arrived at 17:39:14 UTC, so evidence acquisition and the stop decision consumed **5 minutes 28 seconds** of the 2-hour-30-minute active-research ceiling. Report preparation and verification stayed within the same session and did not resume acquisition after the stop.

## Reproduction

The two successful read-only requests can be reproduced with `curl`; later responses may differ because CDX is a live index:

```sh
curl -fsSL -A 'Mozilla/5.0 SignalResearch/1.0' \
  'https://web.archive.org/cdx/search/cdx?url=disclosures-clerk.house.gov%2Fpublic_disc%2Ffinancial-pdfs%2F2025FD.ZIP&from=20250825&to=20250920&output=json&filter=statuscode%3A200&collapse=digest&fl=timestamp%2Coriginal%2Cstatuscode%2Cdigest%2Clength%2Cmimetype'

curl -fsSL -A 'Mozilla/5.0 SignalResearch/1.0' \
  'https://web.archive.org/cdx/search/cdx?url=disclosures-clerk.house.gov%2Fpublic_disc%2Ffinancial-pdfs%2F2025FD.ZIP&output=json&filter=statuscode%3A200&collapse=digest&fl=timestamp%2Coriginal%2Cstatuscode%2Cdigest%2Clength%2Cmimetype'
```

For the response retained in this run, sorting the returned capture timestamps and selecting the last timestamp before `2025-09-01T04:00:00Z` and first at or after `2025-09-15T04:00:00Z` yields `20250706220425` and `20260206225039`. Neither is inside the frozen period; there are no intervening rows. Because the target rule required a first-appearance interval wholly inside September 8–14, the candidate sequence is empty and the stop rule follows deterministically.

## Success-criterion assessment

| Requirement | Assessment |
|---|---|
| Defensible, reproducible bounded House population | **Unsupported.** No usable official-index observation sequence exists for the frozen period in the queried archive inventory. |
| At least one eligible target Event | **Unsupported / not assembled.** The deterministic candidate sequence could not be formed. |
| Original publication/window membership and target cutoff | **Unsupported.** The nearest capture interval spans about seven months; it cannot establish the required 14-day membership or publication precision. |
| Exhaustive peer-candidate scope | **Unsupported / not begun.** There was no bounded candidate population to exhaust. No peer sampling occurred. |
| Official occurrence content and multiplicity | **Untested after the stop.** No PTR artifact was requested. |
| Reporting-member, historical-security, and direction interpretation | **Untested after the stop.** No present-day ticker or other unsupported identity substitution was made. |
| Correction-aware state at contextual cutoff | **Untested after the stop.** No artifact/version or amendment population was assembled. |
| Reproducible Raw Consensus and Other Reporting Members | **Unavailable.** No integer, distribution, or zero was computed. |

## Limitations and exclusions

- CDX is an independent archive index, not the House publication ledger. An empty date-range result establishes no matching preserved capture in that query response; it does not establish that the official index or individual filings were absent or unpublished.
- Distinct-digest collapsing describes the archive query result and may omit repeated captures of identical bytes. Repeated identical captures could establish observation at another time, but the bounded date-range query returned none for the frozen vicinity. No completeness claim is made about Internet Archive collection behavior.
- The plan did not authorize switching to another archive, URL family, period, filing year, chamber, or aggregator after this gate failed. Those possibilities are untested, not silently rejected.
- No current official index body, archived official index body, official PTR, House publication document, exchange calendar, aggregator record, market price, return, benchmark, application database, or production-ingestion path was queried. No market outcome was inspected.
- No source value was normalized or repaired, no filing or transaction date was treated as publication evidence, and no application code or `CONTEXT.md` content changed.

Temporary response bodies and headers reside only under `/tmp/issue25-*` for this session and are not committed as a source corpus. This report preserves their request URLs, retrieval/response times, sizes, hashes, decisive metadata, procedure, and retention limit. It is the sole durable findings asset from this effort.
