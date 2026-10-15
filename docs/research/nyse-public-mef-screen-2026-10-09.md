# NYSE public MEF: bounded research

Observed **2026-10-09 India time** (2026-10-08 UTC). Research only; no code, integration, issue/readiness changes, Git operations, other-provider research or backfill. Inspected [#31](https://github.com/AviSharma01/signal-workspace/issues/31), [conformance contract](../market-data-conformance.md), [#26 §6](https://github.com/AviSharma01/signal-workspace/issues/26) and [prior screen](free-corporate-action-component-screen-2026-10-08.md) first. Success criteria: establish public archive/access/rights and exact observed action semantics, or identify the missing evidence. Sequence: contract → official documentation/terms → tiny current-file inspection → classifications. This is research evidence, not provider approval or conformance certification.

**NYSE public MEF can plausibly contribute current lifecycle notices and selected exchange dates to a free composite. Free 2021–2026 historical public access is NOT established. Original cash-distribution and split coverage is NOT established.**

| Question | Classification | Evidence and limit |
|---|---|---|
| 1. Free public archive, 2021 through completed 2026 sessions | UNKNOWN | No archive URL, date index or public historical query method discovered. Direct public directory contains one current file; samples contain only `dummy.txt`. Absence from this search is not proof no archive exists. |
| 2. Archive access/range/format/version/rights | UNKNOWN | No historical-public files discovered, so none of these archive properties can be established. Current access is unauthenticated HTTPS JSON; no schema version is embedded. |
| 3. Actual public event types/fields | PASS for observed inventory | Eight current records, seven distinct types, detailed below; complete historical/event-type coverage remains UNKNOWN. |
| 4. Required cash/split/identity/provenance fields | Mixed | Field-specific classifications below. |
| 5. Full date semantics, including before-open/after-close | UNKNOWN | Publication/effective/ex-date are distinct observed fields; before-open text is present. No complete public semantic specification or after-close example established. |
| 6. Corrections/cancellations | EMPIRICAL TEST REQUIRED | `is_cancelled` exists but every observed value is false. No observed amendment/revision chain. Public linkage/update behavior remains UNKNOWN. |
| 7. Older observed files retained/replayed | UNKNOWN for durable rights and source retrieval | Local stored bytes are replayable; retaining them looks compatible with the specific free-use grant (inference). Perpetual retention of removed/cancelled versions and an exchange-hosted version archive are not explicit. |
| 8. Public versus commercial/comprehensive products | PASS: distinction established | Commercial API and report products advertise richer content and purchase/subscriber access; their historical/schema claims do not establish free public entitlement. |

Archive search was limited to official NYSE/SEC documentation, targeted searches, the [FTP root](https://ftp.nyse.com/), [public directory](https://ftp.nyse.com/MEF_Public/) and [public samples](https://ftp.nyse.com/MEF_Public_Samples/). No guessed archive enumeration. With no free archive discovered, the conditional historical-file experiment was not performed.

## Exact current observation

One direct HTTP retrieval of [mef_public.json](https://ftp.nyse.com/MEF_Public/mef_public.json) returned **5,999 bytes, count 8, next/prev null**. Types: `suspend` (2), `merger`, `change-underlying-share-ratio`, `admit`, `suspend-voluntary`, `transferable-rights`, `dividend`. These are notices of announced/pending events, not independently verified completed actions. Cached web output showed an older one-record file; the retained direct response governs this observation.

| Field/property | Classification | Exact observed coverage |
|---|---|---|
| Original cash amount | UNKNOWN | ELME dividend exposes `return_of_capital: "1.74000000000000000000"`; original/per-share/adjusted basis is unestablished. No `regular_amount` observed. |
| Currency | FAIL in observed file; UNKNOWN broader public coverage | No currency field in any record. Do not infer USD. |
| Ex/effective date | PASS for presence | `effective_date` and `effective_timing` in six records; absent from merger and ratio-change records. `content.ex_date` in rights and dividend records. |
| Split ratio/factors | FAIL in observed file; UNKNOWN broader public coverage | AMTD `change-underlying-share-ratio` has no ratio/factors. No split record observed. |
| Symbol/listing identifiers | PASS symbol; UNKNOWN historical identity | Security/target symbols CCO, AMTD, OBK, NMCO, ELME. Also DMM, post, panel, status, designation and foreign-private-issuer flag. No CUSIP, exchange or permanent security/listing ID observed. |
| Event ID/publication | PASS for presence | All eight have UUID-shaped `event`, offset-bearing `published_at`, `type` and `content`. Timestamp does not prove original issuer announcement time. |
| Cancellation/amendment | PASS cancellation-field presence; EMPIRICAL TEST REQUIRED behavior | All eight `is_cancelled: false`; no `revisions`, `original` or `related` keys. |

Ordinary lifecycle example: OBK voluntary suspension UUID `82e94c00-28f6-42e0-8015-6b8a7b2de3d9`, published October 8 at 10:42:45.574576 −04:00, effective October 13 before open. CCO suspension additionally says pending before open, subject to merger effectiveness; do not treat it as completed.

Dividend example: ELME UUID `356e0b29-596b-4be5-88d2-256851aada9d`, published October 8 at 07:25:14.955353 −04:00, ex/effective October 23 before open, due bills October 9–22, settlement/off October 23, return-of-capital value above. No currency, regular dividend, record/pay date or original-share-basis guarantee. NMCO rights have September 8 ex/effective date but October 8 publication: never substitute effective date for supported availability.

## Documentation, rights and distinctions

[SEC-published SR-NYSE-2024-68, pp.2–4](https://www.sec.gov/files/rules/sro/nyse/2024/34-101516.pdf) describes listing-venue information (including splits, listings, spin-offs, suspensions/delistings, symbol/name changes, mergers and dividend information), contemporaneous public dissemination, and explicit free use for any party/purpose including redistribution: **PASS**. Its proposed Q4 2024 implementation does not establish a 2021 backfill or public field completeness.

Retention/replay of observed public snapshots looks compatible with that grant **as an inference**, not an explicit perpetual-license finding. [ICE terms](https://www.ice.com/privacy-security-center/terms-of-use) have restrictive general copy/extraction provisions and special-term precedence. The exact relationship to the specific public grant, and durable removed-version retention, warrant clarification. This narrows the prior screen's retention PASS: the explicit free-use grant passes; strict perpetual retention remains UNKNOWN. No rights are inferred for an undiscovered historical archive.

[Commercial MEF](https://www.nyse.com/market-data/corporate-actions/market-event-feed) offers paid historical/real-time queries. Its [factsheet](https://www.nyse.com/publicdocs/nyse/NYSE_Market_Event_Feed_Factsheet.pdf) describes subscriber access, API versioning and revision links/chains. The six-month announcement-before-effectiveness statement is not a free 2021 archive guarantee. [Commercial sample](https://www.nyse.com/publicdocs/nyse/MEF_JSON_SAMPLE.pdf) exposes cash amount/currency, CUSIP and revision fields missing from the observed public file. [Commercial OpenAPI v3.0.0](https://api.nyse.com/docs/api/market-events/market-events-3.0.0.yaml) defines split factors/ratio and ex-date semantics, but `return_of_capital` lacks units/original-basis explanation; API-key entitlement and version cannot be transferred to public JSON. [Comprehensive corporate-action reports](https://www.nyse.com/market-data/corporate-actions) are separately marketed products. None establishes a free comprehensive historical archive.

Smallest next action: request one NYSE clarification identifying the **free public** archive URL/range (including 2021–2023), public schema/update/rolloff/revision rules, original cash/currency/split semantics and durable older-file retention rights. No message sent. Until answered, treat MEF as a conditional current lifecycle/date contributor; #31 readiness stays unchanged.

## Retained research evidence

Exact bytes and HTTP headers are in [research evidence](evidence/nyse-public-mef-2026-10-09/manifest.md), outside application state and fixtures. No historical files or completed-action verification are claimed.

Publication review, **2026-10-15**: the four retained public-file/index/header
artifacts were hash-checked without retrieving a new snapshot. The receipt now
states the specific public-use/redistribution basis and its limits. No commercial
MEF sample, paid provider dataset, issuer workbook or Nasdaq dividend response
is included. This remains a bounded public-subset observation, not an unlimited
historical-retention finding or production certification.
