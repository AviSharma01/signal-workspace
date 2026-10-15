# Free corporate-action component screen

Research observation date: **2026-10-08**. Bounded documentation/decision research; no code changes, provider integration, Git operations, issue changes, or production-readiness changes. Required history remains **2021–2025 plus completed 2026 sessions through evaluation**. No complete historical action inventory or workload was measured here.

Success criteria: inspect the unchanged contract, classify original semantics/coverage/rights using primary evidence, map component responsibilities, and identify one next step. Sequence: contract inspection → official-source screen → focused public examples and terms → comparison and verification of citations. This report is a research recommendation, not an approved ADR, specification change or provider adoption.

Inputs inspected: [#31](https://github.com/AviSharma01/signal-workspace/issues/31), [provider-neutral conformance contract](../market-data-conformance.md), [#26 §6](https://github.com/AviSharma01/signal-workspace/issues/26), [free-provider screen](free-market-data-provider-screen-2026-10-07.md), [Stooq technical screen](stooq-technical-screen-2026-10-07.md), and [Twelve Data Basic screen](twelve-data-basic-screen-2026-10-08.md). Stooq's tested nominal-dividend route fails original-event semantics; Twelve Data's separate actions are paid. This screen therefore assesses **actions-only components**, not another all-in-one API.

**A bounded, evidence-backed free component looks plausible. A complete, retainable 2021–2026 U.S.-listed action ledger is not established.** Original declarations, authoritative exchange dates/lifecycle notices, and separately validated historical identity could form a composite. Complete cash-event discovery, explicit no-action evidence, historical exchange archives and durable raw-version rights remain blockers.

## Four strongest routes

Legend: **P = PASS; F = FAIL; U = UNKNOWN; E = EMPIRICAL TEST REQUIRED**. P is scoped to the stated documented property or observed example, never a complete #31 gate certification. E means validation is warranted, not that legal U can be ignored. D = documented fact; I = inference.

| Criterion | Original EDGAR + issuer/Form 8937 | NYSE public MEF | Nasdaq Events Data | Alpaca actions-only |
|---|---|---|---|---|
| Original cash amount, ex-date, currency | E: declarations preserve amounts; ex-date/currency often missing | U: cash schema/examples unverified | F: free Ex-Date subset is no complete cash ledger | U: original basis/currency not guaranteed |
| Original split terms and date meanings | P for observed NVDA; E generally | U | U: issuer supplement needed | E: explicit factors/ex-date |
| Required historical coverage | P archive span; E action completeness | U: no historical index found | U: historical subset unestablished | U: current endpoint history unestablished |
| Security identity/joinability | E: dated class/ticker/exchange; CIK identifies filer | U: symbol/event ID insufficient alone | U: dated symbol/issue metadata, no permanent ID | E: IDs/CUSIPs; historical joins untested |
| Delisted/terminal/noncash support | P observed TWTR; E completeness | E: actual suspension record | E: lifecycle subset | E: documented action types |
| Revisions/older versions | P amendment/PAC behavior; U old removed versions | E: cancellation/publication fields | E: distribution timing; full corrections U | U: revisions/publication vintages |
| Provenance | P accession/doc/source; availability needs care | P observed event UUID/published time | P authoritative exchange subset; timing E | U upstream authority; E vendor IDs |
| Raw/version/derived retention rights | P EDGAR public-filing reuse; U complete version coverage/non-SEC copies | P free subset grant; archival reading I | P named free subset grant; archival reading I | U |
| Zero-cost feasibility | P access; E complete workload | P public file; U historical access | P subset; U historical access | U free action entitlement/geography |

### 1. Original SEC filings plus issuer disclosures: strongest semantic evidence

**D:** EDGAR permits free downloads, indexes since 1994Q3, bulk access and declared automated requests up to 10/second. CIKs are nonrecycled **filer** identifiers. Post-acceptance corrections/removals occur; indexes can change. Archive depth proves neither complete action extraction nor an immutable history. [SEC access documentation](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).

**D, concrete examples:** NVIDIA's contemporaneous May 2021 exhibit preserves **$0.16/share**, July 1 payment and June 10 record date; it does not supply an ex-date. NVIDIA's June 2024 8-K gives **10:1**, legal effectiveness June 7 at 16:01 Eastern and split-adjusted trading June 10. Its issuer FAQ explicitly gives June 11 ex-dividend and **$0.01/share on that event's post-split basis**. Preserve those original bases; do not retrospectively divide 2021 cash by later splits. A bare dollar sign still needs supported currency interpretation. [Original 2021 exhibit](https://www.sec.gov/Archives/edgar/data/1045810/000104581021000063/q1fy22pr.htm), [2024 split filing](https://www.sec.gov/Archives/edgar/data/1045810/000104581024000144/nvda-20240607.htm), [issuer FAQ](https://investor.nvidia.com/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf).

**D:** Twitter's retained 2022 8-K identifies common stock/TWTR/NYSE, October 27 merger cancellation for $54.20 cash, and suspension before October 28 open. Its index distinguishes report date October 27, acceptance October 28 20:22:36, and filing date October 31. Acceptance cannot automatically establish public availability; retrieval time proves only local observation. Under #26, retaining these terminal terms still does not authorize a numeric terminal return. [TWTR filing](https://www.sec.gov/Archives/edgar/data/1418091/000119312522272772/d411753d8k.htm), [filing index](https://www.sec.gov/Archives/edgar/data/1418091/000119312522272772/0001193125-22-272772-index.htm).

**D:** Form 8937 covers basis-affecting actions, including splits/nontaxable distributions, and explicitly excludes dividends reportable on Form 1099-DIV. Website posting is an alternative to IRS filing, with ten-year public availability including successors; corrected reporting is required. This is a publishing obligation, not a consumer retention license or universal public IRS database. Forms request action date, class, CUSIP/ticker and quantitative terms; action date is not necessarily exchange ex-date. [IRS instructions](https://www.irs.gov/instructions/i8937), [form fields](https://www.irs.gov/pub/irs-pdf/f8937.pdf), [NVIDIA's 2021/2024 form library](https://investor.nvidia.com/investor-resources/faqs/).

**Hard limits:** Companyfacts/frames alone are not a corporate-action ledger: standard-taxonomy, entire-entity facts omit custom/class contexts, and frames select latest-filed matching facts. Routine dividends are not a mandatory universal 8-K action inventory; Item 8.01 is discretionary. Absence of filings cannot become explicit no-action evidence. [SEC API semantics](https://www.sec.gov/search-filings/edgar-application-programming-interfaces), [official Form 8-K](https://www.sec.gov/files/form8-k.pdf).

**Rights clarification, 2026-10-15:** SEC's [reuse FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions) expressly permits reuse of EDGAR public filing content; its [dissemination policy](https://www.sec.gov/about/privacy-information#website-dissemination) permits copying/distribution and requests appropriate attribution. The earlier access-only assessment was incomplete. Complete historical/removed-version availability and replay remain unproved. Non-SEC issuer-site terms are separate: NVIDIA allows limited personal use and includes extraction/termination restrictions. Do not extend SEC permission to issuer-site copies or infer that access establishes a complete action inventory. [NVIDIA terms §§3,6](https://www.nvidia.com/en-us/about-nvidia/terms-of-service/).

### 2. NYSE public Market Event Feed: strongest explicit free-use grant

**D:** NYSE's rule filing says exchange-received information is publicly accessible without charge and usable by any party for any purpose, including redistribution. **I:** this supports local raw snapshots, observed versions and derived outputs for the expressly public subset; it does not grant the priced MEF service or a historical archive. [NYSE rule filing, pp. 2–3](https://www.sec.gov/files/rules/sro/nyse/2024/34-101516.pdf), [separate commercial MEF](https://www.nyse.com/market-data/corporate-actions/market-event-feed).

**D, bounded inspection:** the [public directory](https://ftp.nyse.com/MEF_Public/) exposed one [JSON file](https://ftp.nyse.com/MEF_Public/mef_public.json), not a historical index. A MID voluntary-suspension entry exposed event UUID, symbol, effective date October 12, 2026, before-open timing, publication October 7 with Eastern offset and cancellation status. This supports lifecycle/provenance schema, not cash/split semantics, a complete terminal inventory or 2021 coverage. The public [Ex-Date page](https://www.nyse.com/trade/ex-date-dividends) supplies due-bill exceptions rather than all distributions. No historical backfill was attempted.

Publication review, **2026-10-15**: the later [public-MEF check](nyse-public-mef-screen-2026-10-09.md) narrows the table's rights classification. PASS concerns the express public-use/redistribution grant only; perpetual removed-version retention remains UNKNOWN. The MID example was an earlier browser observation, not a row in the separately retained eight-record snapshot. No complete archive or dividend component is established.

### 3. Nasdaq Events Data: free exchange dates/status evidence

**D:** Nasdaq expressly excludes specified Events Data from general restrictions. The free status/ex-date subset is useful for dated additions, suspensions and issue changes. Ex-Date publication covers exceptions where ex-date differs from record date, not a complete cash ledger. Current tables cannot establish 2021 archive access or permanent security identity. [Rights notice](https://www.nasdaqtrader.com/trader.aspx?id=symbollookup), [status updates](https://www.nasdaqtrader.com/Trader.aspx?id=nasdaq-security-status-updates), [Ex-Date limitations](https://www.nasdaqtrader.com/Trader.aspx?id=nasdaq-ex-date).

**D:** SR-NASDAQ-2026-062 describes a free FTP subset including ex-date/status/issue events and distribution timing. Deployment/access details remain U; the filing does not make historical paid Daily List records free. **I:** unrestricted named-subset use supports snapshot/derived retention; no extension to Nasdaq.com APIs or the priced Daily List is justified. Pair supported exchange dates with original issuer terms, never infer missing dates from record dates. [2026 filing](https://www.sec.gov/files/rules/sro/nasdaq/2026/34-106034.pdf), [commercial Daily List](https://classic.nasdaqtrader.com/Trader.aspx?id=DailyListPD).

### 4. Alpaca corporate actions: conditional structured lead

**D:** The actions endpoint documents splits, cash/stock dividends, spin-offs, mergers and worthless-security removal. Queries use **process_date**, not event ex-date; default complete-data filtering excludes unprocessed incomplete records, while processed records can still be incomplete. Creation timing and vendor delays do not certify historical publication. Its official model supplies split old/new factors and ex-date, and dividend rate/ex-date/symbol/CUSIP, but no cash-currency field. Original-versus-adjusted cash guarantees and upstream event authority remain U. [Endpoint](https://docs.alpaca.markets/us/reference/corporateactions-1), [official model](https://raw.githubusercontent.com/alpacahq/alpaca-py/master/alpaca/data/models/corporate_actions.py).

The old announcements API's April 2020 history claim does not certify the current market-data endpoint. Current free action entitlement, applicable geographic access, perpetual raw/version/derived retention and correction behavior require clarification. General terms describe free Basic personal noncommercial use and a U.S.-resident restriction; no blanket raw-data deletion conclusion is established here. The prior **daily-bar** failure does not reject a separate actions component. [Old API announcement](https://alpaca.markets/blog/introducing-corporate-actions-api-announcements/), [terms](https://files.alpaca.markets/disclosures/library/TermsAndConditions.pdf).

## Other serious candidates and hard disqualifiers

Same nine criteria, scoped to these routes: C cash; S splits; H history; J identity/join; T terminal; R revisions; P provenance; L retention; Z zero cost.

| Candidate | C | S | H | J | T | R | P | L | Z |
|---|---|---|---|---|---|---|---|---|---|
| FINRA licensed OTC Daily List API | E | E | U | E | E | U | P | U | P access; E workload |
| OCC public information memos | F ordinary ledger | E | U | E | E | E | P | F automated route | F compliant automation |
| Massive Basic actions | E | E | F required history | E | U | U | U upstream | U | P short-history access |

**FINRA:** documented OTC records include cash text, ex-date, split rates, identifiers and old/new symbols/CUSIPs. This is an OTC/lifecycle supplement, not the required listed-equity ledger. Website storage/database/scraping restrictions reject that website route. The **licensed API differs**: noncommercial use and derivatives are allowed; redistribution requires FINRA attribution, no incremental charge and no further redistribution by recipients. Data-retention entry is N/A. API termination deletes API copies and stops retransmission, not necessarily all public raw data. Permanent/version retention remains U; do not falsely reject the API using website terms. [Schema](https://developer.finra.org/docs), [website terms](https://www.finra.org/terms-of-use), [equity-specific API terms](https://developer.finra.org/specific-terms-equity-data), [API terms §10.5](https://developer.finra.org/finra-api-terms-service). **D:** individuals can obtain Public credentials for public data at no charge, capped at 10 GB/month; required backfill/catch-up feasibility remains E. [Current API FAQ](https://developer.finra.org/support).

**OCC:** memos substantiate optionable underlying split/special/terminal terms, not ordinary cash-dividend completeness. Its website expressly prohibits automated extraction; no durable archival grant was established. Reject that automated route. [OCC terms, restrictions (p)](https://www.theocc.com/specialpages/legal/terms-and-conditions), [example memo](https://infomemo.theocc.com/infomemos?number=54262).

**Massive:** new actions endpoints distinguish original cash from split-adjusted cash and are offered across plans, but Basic split history is limited to two years. That actions-specific history conflict rejects it as the 2021–2026 component, independently of price-plan failures. [Action endpoint announcement](https://massive.com/blog/new-splits-and-dividends-endpoints), [split history entitlement](https://massive.com/knowledge-base/article/does-massive-support-normal-and-reverse-splits).

## Exact #31 responsibilities and unresolved gates

| Responsibility | Plausible contributor; limits |
|---|---|
| `split_handling`, `cash_distribution_handling` | Original filings/issuer terms + supported exchange dates; Alpaca structured terms conditional. Complete cash inventory/currency U. |
| `non_cash_actions`, `terminal_events` | SEC/8937 terms + exchange lifecycle; Alpaca conditional. Unsupported windows remain unavailable; no invented continuation/terminal return. |
| `currency_units` | Only explicit supported currency/units; dollar signs, tax basis figures or option deliverables cannot silently substitute. |
| `provenance_completeness`, `temporal_boundaries` | SEC accession/doc, NYSE UUID/publication, Nasdaq distribution metadata; preserve publication versus retrieval/date meanings. No full gate passed. |
| `historical_security_identity`, `identity_calendar_joins` | Dated class/listing/symbol/CUSIP evidence only; historical intervals and exact session joins still require another validated layer. |
| `historical_coverage`, `retention_rights`, `zero_cost_feasibility` | EDGAR archive span and free exchange grants contribute; complete actions/archive access and workload remain unresolved. |
| `revision_correction`, `repeated_retrieval_versions`, `revision_refresh_validation`, `reproducibility` | Retain/replay original observed inputs if permitted; separately scope corrections. Action correction documentation passes no bar-revision or bounded-refresh gate. |

All routes still need safe joins, independent expectations, observed revision/preservation cases, explicit no-action versus unknown coverage, retained-input semantic replay and measured backfill/catch-up/storage workload. Discovery timestamps cannot reconstruct 2021 knowledge vintages. Current identifiers cannot establish historical identity. None supplies all remaining market-data gates or changes #31 production readiness.

The contract requires preserving earlier versions actually observed, not reconstructing every version a source ever published. Source availability/freshness, publication time, effective/ex-date, filing acceptance and local retrieval are separate observations. Hashes can identify observed changes if retention is permitted; they establish neither amendment relationships nor past public availability.

## Decision and single smallest next clarification

Prioritize **original EDGAR/issuer terms + NYSE public MEF**, with Nasdaq's named subset as complementary exchange evidence; keep Alpaca actions-only conditional. A defensible limited-scope component is realistic. Universal complete, retainable history remains unproven, especially ordinary cash distributions and evidence that no relevant action was omitted.

**Ask NYSE for the exact free historical-public-MEF location/access covering 2021 through completed 2026 sessions, and whether those original records expose cash amount/currency, split factors and date semantics under the same unrestricted public-use grant.** This is one clarification, not a paid-service request or broad provider search. No message was sent. A current JSON example is not a historical coverage experiment, license acceptance, conformance pass or production approval.
