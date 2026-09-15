# Congressional disclosure source evidence

Evidence date: **2026-09-15**. Status: research evidence, not an approved source strategy or methodology.

Ticket: [Establish disclosure source coverage and provenance evidence](https://github.com/AviSharma01/signal-workspace/issues/3).
Prerequisite: [Set V2 research objectives and operating constraints](https://github.com/AviSharma01/signal-workspace/issues/2#issuecomment-5677296093) (approved resolution read on evidence date).

## Scope and evidence standard

Bounded documentation review and read-only availability checks. No bulk dataset ingestion, account creation, purchase, source refresh, or source selection occurred. The target is both chambers, preferably 2012–present, with a minimum of 2021–2025 plus 2026; core recurring data cost must be $0 unless explicitly approved. House-only is permissible with an explicit Senate limitation. These are inherited constraints, not conclusions of this research.

**Documented** means a source owner says it; it does not establish measured completeness or an operating SLA. **Observed** means the specified check returned the described result on the evidence date. **Inference** identifies implications of those facts. All prices and source claims below are as read on 2026-09-15. Search-index extracts and live retrieval are distinguished where they differed. No complete year/chamber inventory or historical first-publication audit was performed.

## Decision-useful findings

- Official portals offer the strongest direct artifact provenance, but the checks do **not** certify a complete 2021–present panel, much less 2012–present. Years in a menu are not counts of eligible filings.
- Filing, transaction, notification, digital-signature, provider-refresh, and first-observed dates are different evidence. None of the inspected interfaces established an audited historical first-public timestamp for every filing or amendment.
- Free Capitol Trades website history (three years) and CongressInvests advertised history (365 days) are individually insufficient for the approved minimum. Quiver's API is advertised from $30/month; its public dashboard is a separate surface.
- Successful health requests can coexist with stale or ambiguous cache metadata and an inaccessible trade feed. A bounded CongressInvests check demonstrated precisely that.
- A source decision can use this evidence, but any declaration of complete coverage or reliable daily catch-up needs an explicit subsequent validation scope. No provider is selected here.

## Source comparison

| Source | Documented coverage/interface | Evidence and constraints | Unestablished |
|---|---|---|---|
| Official House Clerk | Official search exposes filing years including 2012, 2021 and 2026. Search-index copy of landing page lists annual download links 2008–2026. Individual PTR PDFs are public. | Live search HTTP 200; one 2026 PDF inspected. Original filing ID and raw PDF directly available. Usage restrictions on search page. | Annual archive contents, full year/member coverage, machine API contract, update SLA, persistent row IDs, first-public timestamps and amendment linkage completeness. |
| Official Senate eFD | Portal says 2012–present for Senators/former Senators/candidates. Interactive access agreement; reports also available at Office of Public Records kiosk. | Portal documentation retrieved via web; direct search request returned HTTP 403 here. Portal describes member retention until six years after leaving Congress. | Successful automated search from this environment, retained reports for every departed member, full HTML/paper mix, stable row IDs, revision lineage, exact publication timestamps. |
| Quiver Quantitative | First-party source page describes parsing House and Senate disclosures; authenticated API and public Congress dashboard. | API landing page says starting $30/month; setup requires API key and illustrates a paid Hobbyist signup. | Earliest reliable year, complete raw filings, stable row/filing identifiers, amendments, historical first-seen, export/retention rights, precise included plan and billing conditions. No authenticated data tested. |
| Capitol Trades / 2iQ | First-party disclaimer names official sources and caps website history at past three years. About page describes automated and manual collection and free public site. | Claimed delivery as close to real time as possible, without measured SLA; trade page fetch returned 403 in this tool. | API/export contract, longer licensed history/cost, raw snapshots, row IDs, amendment policy, retention permission, historical availability. |
| Senate Stock Watcher origin repository | Owner README documents JSON/YAML daily summaries and aggregates, PTR links and received-date field. | Latest default-branch commit observed as March 2021. README explicitly says scanned PDF filings may have empty transaction arrays. | Fresh ongoing feed, 2021–present coverage, completeness of historical backfill, raw artifact archive and licensing rights. |
| CongressInvests (unverified candidate) | Landing page claims both chambers, 365 days, free 100 requests/day and Pro $29/month; GET health/status/trades interfaces. | Health/status 200, but trade sample 429. Cache metadata internally needs interpretation. No independent row validation. | Provenance accuracy, completeness, amendment handling, stable IDs, storage/redistribution rights, refresh semantics and reliable operation. |

Sources: [House search](https://disclosures-clerk.house.gov/FinancialDisclosure/ViewSearch), [House landing page](https://disclosures-clerk.house.gov/FinancialDisclosure), [Senate portal](https://efdsearch.senate.gov/search/home/), [Quiver sources](https://www.quiverquant.com/datasources/), [Quiver API pricing](https://api.quiverquant.com/), [Quiver setup](https://www.quiverquant.com/api-setup/), [Capitol Trades disclaimer](https://www.capitoltrades.com/disclaimer), [Capitol Trades about](https://www.capitoltrades.com/about-us), [Stock Watcher README at inspected commit](https://github.com/timothycarambat/senate-stock-watcher-data/blob/384e08e84d809477cdfba7d52479147fbe5e6bd7/README.md), [CongressInvests](https://congressinfor-production.up.railway.app/).

## Official sources: provenance and dates

### House

**Observed:** [PTR 20034521](https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/20034521.pdf) is a two-page PDF carrying Filing ID 20034521. Its extracted content includes owner, asset/ticker/type, transaction type, transaction and notification dates, amount range, filing status, subholding owner and a digital signature. This sample's transaction date is April 15, notification date May 1 and signature May 13, 2026. It demonstrates distinct dates, not a publication timestamp. A printed ID column was present, but this extraction did not establish a stable per-transaction identifier.

**Documented:** House accepts electronic or paper PTRs, including amendments. Its paper PTR form distinguishes initial/amended report and asks for the date of the report being amended. General House amendment guidance says an amendment may be a letter and that original and amendment are public. Do not assume every amendment is a replacement table. [Current disclosure guidance](https://ethics.house.gov/financial-disclosure/), [PTR form](https://ethics.house.gov/wp-content/uploads/2024/11/Final-PTR-Form-CY-2023.pdf), [amendment guidance](https://ethics.house.gov/manual/filing-deadlines-committee-review-and-amendments/).

**Observed limitation:** The search-index extract of the landing page contained annual download links; live HTML and web-open subsequently returned a generic Clerk navigation shell. Live ViewSearch still returned 200 and year choices. No ZIP downloaded: this report does not assert whether annual downloads contain indexes, PDFs, or both. The advertised bulk-XML/per-PDF flow on CongressInvests is that candidate's claim, not independently verified official interface documentation.

### Senate

**Documented:** The portal specifies reports filed from 2012 onward and retention for Senators until six years after they cease membership; candidate reports have a different period. The Ethics overview also states a general six-year-after-receipt rule while repeating online access since 2012. These differently scoped descriptions should not be collapsed into a guarantee of an enduring complete archive. The portal's member-specific statement is particularly relevant to survivorship gaps. [Portal](https://efdsearch.senate.gov/search/home/), [Ethics overview](https://www.ethics.senate.gov/public/index.cfm/financialdisclosure).

**Documented:** The Ethics overview says reports are publicly available within 30 calendar days of filing; unsolicited and requested amendments exist, filed by the same electronic/paper method as the original. This is a stated publication bound, not observed compliance or proof of a filing-day event anchor. [Ethics overview](https://www.ethics.senate.gov/public/index.cfm/financialdisclosure).

**Observed limitation:** `GET https://efdsearch.senate.gov/search/` returned HTTP 403 Access Denied from the local network on the evidence date. The `/search/home/` page was retrievable with the web tool. This is an environment/path-specific access result, not proof that Senate data are generally unavailable. No access-control bypass or agreement submission was attempted.

**Documented by dataset owner, not independently sampled at the Senate:** Stock Watcher describes report URLs `/search/view/ptr/<opaque-id>/`, `date_recieved` (owner's spelling), and transaction arrays. It admits paper scans can appear as reports with empty arrays. Thus an empty array need not mean no reported trades. [Owner README](https://github.com/timothycarambat/senate-stock-watcher-data/blob/384e08e84d809477cdfba7d52479147fbe5e6bd7/README.md).

## Aggregator detail and bounded checks

### Quiver and Capitol Trades

Quiver's API setup demonstrates Bearer authentication and `/beta/bulk/congress/politicians` with chamber and pagination parameters; that is a politician-list example, not evidence for a complete historical transaction schema. Its JavaScript docs page yielded no readable specification in the web tool. No key or subscription was acquired. The public dashboard distinguishes filed and traded columns. Advertised API entry price is $30/month, not a verified quote for all required data and rights. [API setup](https://www.quiverquant.com/api-setup/), [API landing page](https://api.quiverquant.com/), [dashboard](https://www.quiverquant.com/congresstrading/).

Capitol Trades advertises human quality assurance alongside automated collection and near-real-time delivery. Those are provider claims; this session did not compare a trade to an official filing or measure delay. Its three-year website limit is explicit. It could be a cross-check candidate, but free browsing does not establish a bulk extraction or retention license. [About](https://www.capitoltrades.com/about-us), [disclaimer](https://www.capitoltrades.com/disclaimer).

### Stock Watcher and other access limitations

`gh api repos/timothycarambat/senate-stock-watcher-data/commits` returned latest commit `384e08e84d809477cdfba7d52479147fbe5e6bd7`, dated `2021-03-16T18:13:53Z`. This establishes the inspected repository's age, not the state of every Stock Watcher distribution. No aggregate file was ingested. [Commit](https://github.com/timothycarambat/senate-stock-watcher-data/commit/384e08e84d809477cdfba7d52479147fbe5e6bd7).

House Stock Watcher's API page returned a web-tool 502, and the guessed same-owner `house-stock-watcher-data` repository returned 404. These bounded failures do not establish that the service went dark in a particular year or that no mirror exists. Finnhub's congressional-trading documentation URL returned 429 in the web tool; coverage, costs and schema remain unverified here. These candidates were not promoted on secondary claims. [House API attempted](https://housestockwatcher.com/api), [Finnhub docs attempted](https://finnhub.io/docs/api/congressional-trading).

### CongressInvests: unverified candidate

**Documented, 2026-09-15:** Landing page claims a 365-day in-memory cache, source links in example rows, and stock/options filtering. It advertises six-hour updates but also says automatic cache refresh every 24 hours. Free access claims 100 requests/day; Pro is advertised at $29/month. No stable row ID, amendment flag/lineage, or immutable raw snapshot is established by the example. [Landing page](https://congressinfor-production.up.railway.app/).

**Observed, 2026-09-15, approximately 09:29–09:31 UTC:** GET `/health` and `/cache/status` each returned HTTP 200 with `status: ok` (health), `ready: true`, `loading: false`, 1004 tickers, `last_updated: 2026-09-10T03:13:06Z`, `age_seconds: 454552`, `data_lag_minutes: 7576`, and `next_refresh_in_minutes: 0`. Both exposed `senate_last_scraped_at: 1789463732.5703945` and `house_last_scraped_at: 1789463732.8745372`, much newer than `loaded_at: 1789009986.998161`. Those are returned field values, not verified successful source retrievals. [Health endpoint](https://congressinfor-production.up.railway.app/health), [cache status](https://congressinfor-production.up.railway.app/cache/status).

A single-row request to `/trades/recent?limit=1&days=30` returned an error body saying the daily limit of 100 was exceeded; a repeat to capture HTTP status returned 429 at `2026-09-15T09:31:02Z`. Only these two sample attempts were made. The quota scope (for example shared egress) is unknown. No trade was verified and no refresh POST was called. [Sample endpoint](https://congressinfor-production.up.railway.app/trades/recent?limit=1&days=30).

**Inference:** Health success is separate from data access, and fresh scrape-at fields do not resolve old loaded-at metadata. The metadata could reflect different refresh stages; it does not prove either fully stale trades or successful freshness. Its advertised short history alone fails the main historical minimum. Retain candidate status.

## Access, retention and downstream implications

**Documented:** Both official access pages prohibit specified uses, including commercial purposes except news/communications dissemination, credit-rating use, and solicitation. This report records the displayed restrictions without giving a legal determination of intended use. Neither free access nor an aggregator's pricing page establishes unrestricted redistribution, permanent retained-copy rights, or permission for all automated use. [House access notice](https://disclosures-clerk.house.gov/FinancialDisclosure/ViewSearch), [Senate access notice](https://efdsearch.senate.gov/search/home/). Vendor storage/export rights and any paid adoption remain unresolved; no contact or transaction occurred.

The following are **decision implications**, not adopted architecture:

1. To make provenance reviewable, evaluate retaining the exact retrieved official PDF/HTML, index/search evidence, source URL and native filing ID, fetch timestamp, content hash and parsing version. Retain aggregator responses separately from original artifacts. Preserve raw fields separately from normalization and eligibility.
2. A possible fallback row locator is filing artifact identity plus page/table/row position and raw-content hash. This is not an official row ID and is unstable when documents change. Ticker/date/amount alone cannot safely equate two records. Cross-source identity and amendment lineage need their own decision.
3. Keep reported transaction, notification and filing/signature dates separate from observed retrieval/first-seen and provider cache dates. A current download proves availability now only. Without contemporaneous observations or trustworthy archival evidence, exact past public availability and overwritten pre-amendment states may be irrecoverable. Do not silently substitute current corrected rows into earlier as-of analyses.
4. Daily discovery and catch-up can be an operational target, but none of the bounded checks proves a reliable full discovery watermark. Reachability, parsing success, per-chamber coverage, last successful discovery, provider metadata age and transaction recency need separate interpretation. An empty/blocked/partial response must not certify no new disclosures.
5. Source strategy must decide what achievable coverage claim is defensible, which artifacts and access terms suffice, and what explicit degradation applies when Senate access or an aggregator fails. A House-only or exploratory result must expose the coverage limitation. An oldest row, menu year or stated historical range is insufficient to certify a complete common panel.

## What remains unknown

No verified minimum-coverage dataset, provider completeness ranking, amendment reconciliation rate, machine-resource benchmark, official polling SLA, historical publication-time archive, or cross-source duplicate match was established. Future bounded validation can inventory specific years and representative initial/amended/paper filings after scope approval. This research provides source-strategy inputs and explicit gaps; it authorizes no ingestion implementation, event anchor, provider purchase or methodology change.
