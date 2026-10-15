# Bounded historical-security-identity feasibility and workload experiment

Observation date: **2026-10-09**. Research/validation only. No production code,
provider integration, GitHub issue, readiness state, approved V2 semantic, or Git
state was changed. The experiment is the six required cases only; it is not a
U.S. security-master construction or population-wide scalability claim.

Documentation review, **2026-10-15**: corrected the TWTR pre-open availability
claim and related acceptance/eligibility language. The economic dates and
recorded acceptance times remain unchanged. Public availability not established
by the cited evidence remains UNKNOWN; no new historical observation is invented.

## Decision

**Historical identity is validated PLAUSIBLE for a bounded, event-derived Signal
population, but remains UNRESOLVED for complete population coverage and #31
readiness.** All six cases can be represented without ticker conflation when
issuer/filer, security/share class, listing, ticker assignment, effective bounds,
and evidence timing are separate records. No case justifies a ticker as a permanent
key, and no missing bound was filled from current metadata, name/price similarity,
CIK alone, OpenFIGI alone, or absence of another candidate.

The six-case workload was approximately one focused research day: about **20
core primary-source documents, 21 independent joins/reconciliations, and 11 manual or
ambiguous decisions**. Once the documents are retrieved, the explicit rename,
class, listing-commencement, and terminal assertions are deterministic to extract.
Discovery completeness, unchanged-interval claims, source-rights review, historical
publication eligibility, and conflicting or sparse evidence remain manual. This
is reasonable for a solo project only if Signal resolves the bounded population
actually encountered in disclosures and reuses evidence patterns. It is not shown
reasonable for a prebuilt complete U.S. master.

## Authority, method, and classifications

First inspected: [#31](https://github.com/AviSharma01/signal-workspace/issues/31),
the [provider-neutral market-data contract](../market-data-conformance.md), approved
[#26 / V2 market-data semantics](../specs/signal-v2.md#6-benchmark-and-return-semantics),
the earlier [identity screen](historical-security-identity-screen-2026-10-09.md),
[OpenFIGI META/METV experiment](openfigi-meta-metv-experiment-2026-10-09.md),
[calendar validation](exchange-session-calendar-validation-2026-10-09.md), and
[ordinary-cash-dividend validation](free-ordinary-cash-dividend-validation-2026-10-09.md).
The then-current synthesis draft was also a historical input; the final synthesis
is downstream of this experiment and is not an independent expectation.

The unchanged boundary requires historically scoped security/listing mappings,
retained evidence and revisions, independent expectations, and fail-closed
handling of reuse and terminal events. Identity evidence does not activate market
capabilities or authorize a numeric terminal return.

**PASS** means directly supported for the stated case and bound. **FAIL** means
the observed route is incompatible. **UNKNOWN** means the necessary evidence is
absent. **EMPIRICAL TEST INCONCLUSIVE** means the bounded panel or lookup did not
establish the property. A source's filing date/acceptance is kept separate from
the event's economic effective time and this experiment's 2026-10-09 retrieval.
SEC explains that EDGAR acceptance timestamps are system-assigned and that public
filings are disseminated, but it exposes no timestamp proving the first moment a
filing appeared on sec.gov. A dated document or acceptance before an economic
boundary is not by itself proof that the exact version was publicly available
by that boundary. Dated issuer/exchange statements are preserved as evidence
with their stated precision; unsupported public-information eligibility remains
UNKNOWN. [SEC timestamp guidance](https://www.sec.gov/about/webmaster-frequently-asked-questions),
[EDGAR access/dissemination](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data).
All source reads in this experiment were observed on 2026-10-09 IST; exact
per-request retrieval timestamps were not retained and are therefore **UNKNOWN**.
The two ETF cases are required identity stress controls, not additions to V2's
approved individual-equity Analysis population.

## Case evidence chains

### 1. Meta Platforms Class A: `FB` to `META`

- **Issuer/filer:** Meta Platforms, Inc., CIK `0001326801` (**PASS**).
- **Security/listing:** Class A common stock, Nasdaq Global Select Market
  (**PASS**). The 8-K cover still reports `FB`; the filing and exhibit say the same
  class begins trading as `META` before the June 9, 2022 market open. Nasdaq's
  June 3 alert independently names old/new symbols, class, unchanged CUSIP, and
  marketplace-effective date. [May 31 8-K and filing metadata](https://www.sec.gov/Archives/edgar/data/1326801/000132680122000070/0001326801-22-000070-index.htm),
  [issuer-filed exhibit](https://www.sec.gov/Archives/edgar/data/1326801/000132680122000070/may312022-exhibit991.htm),
  [Nasdaq alert](https://www.nasdaqtrader.com/TraderNews.aspx?id=ECA2022-125).
- **Validity:** a contemporaneous Form 8-A establishes the approved `FB` class,
  symbol and Nasdaq venue, and the issuer's 2013 10-K says trading began on
  **2012-05-18**. `FB` ends / `META` starts at the supported before-open boundary
  on **2022-06-09** (**PASS**). The still-current `META` assignment's end is
  **UNKNOWN/open**. [2012 Form 8-A](https://www.sec.gov/Archives/edgar/data/1326801/000119312512230161/d350836d8a12b.htm),
  [2013 Form 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000132680114000007/fb-12312013x10k.htm).
- **Dated availability evidence:** the 8-K was accepted 2022-05-31 16:18:52 and
  the exchange alert is dated 2022-06-03, both before the effective date.
  Acceptance is not first-public availability. The 2012 Form 8-A records the
  approved class/symbol/venue, while the exact 2012-05-18 trading date is evidenced by
  the later 2013 10-K and therefore is retrospective at that original As-Of.
  Exact first-public instants remain **UNKNOWN**.
- **OpenFIGI:** the retained 2026 observation matched Meta Platforms Class A with
  composite FIGI `BBG000MM2P62` and share-class FIGI `BBG001SQCQC5` (**PASS as
  current enrichment only**). It supplies no historical interval.

### 2. Roundhill ETF: historical `META` to `METV`

- **Issuer/filer and class:** Listed Funds Trust, CIK `0001683471`; Roundhill Ball
  Metaverse ETF, SEC series `S000072321`, class/contract `C000228445` (**PASS**).
- **Security/listing:** a June 28 SEC prospectus identifies the fund as `META` on
  NYSE Arca, and a June 30 launch release reports `NYSE: META`; the January 14,
  2022 SEC supplement identifies the same fund and changes `META` to `METV` upon
  the January 31 open (**PASS** for the relationship and rename). [SEC summary prospectus](https://www.sec.gov/Archives/edgar/data/1683471/000089418921004134/roundhillmetasummaryprospe.htm),
  [dated launch release](https://www.roundhillinvestments.com/assets/pdfs/meta_press_release.pdf),
  [SEC supplement](https://www.sec.gov/Archives/edgar/data/1683471/000089418922000256/meta497etickerchange.htm),
  [SEC series/class filing metadata](https://www.sec.gov/Archives/edgar/data/1683471/000089418922003398/0000894189-22-003398-index.htm).
- **Validity:** the fund's later SEC shareholder report says operations commenced
  **2021-06-29**, while the issuer launch release is dated June 30; no located
  contemporaneous exchange notice fixes the first exchange-trading instant. The
  exact `META` listing start is therefore **UNKNOWN**. `META` ends and `METV`
  starts at the **2022-01-31** open (**PASS**). `METV`'s end is **UNKNOWN/open**.
  [SEC shareholder report](https://www.sec.gov/Archives/edgar/data/1683471/000113322825002437/rlf-efp14667_ncsr.htm).
- **Dated availability evidence:** the June 28 prospectus date precedes the
  reported operations commencement, and the January 14 supplement date precedes
  the rename. Those dates alone do not certify first-public availability. The
  June 30 launch release is not backdated to June 29. Exact first-public
  timestamps and any unsupported historical eligibility are **UNKNOWN**.
- **OpenFIGI:** the retained 2026 result returned a distinct ETF pair,
  `BBG011J1MN62` / `BBG011J1MP12`. Separation from Meta Platforms is **PASS**;
  the exact historical-to-current fund name/class crosswalk is **EMPIRICAL TEST
  INCONCLUSIVE**, so the identifiers remain optional candidates.

### 3. Later reused `FB`: ProShares S&P 500 Dynamic Buffer ETF

- **Issuer/filer and class:** ProShares Trust, CIK `0001174610`; series
  `S000093206`, class/contract `C000261360`, ProShares S&P 500 Dynamic Buffer ETF
  (**PASS**). The SEC Form 497 was accepted 2025-06-23 and reports ticker `FB`.
  [SEC filing metadata](https://www.sec.gov/Archives/edgar/data/1174610/000168386325005265/0001683863-25-005265-index.htm).
- **Listing and start:** Cboe BZX Information Circular 25-343, dated June 25,
  identifies the fund, ticker `FB`, ProShares Trust, primary Cboe BZX listing, and
  commencement of exchange trading on **2025-06-26** (**PASS**). [Cboe circular](https://cdn.cboe.com/resources/regulation/circulars/products/IC_2025-343.pdf).
- **Inception versus listing:** issuer/SEC materials report a **2025-06-24** fund
  inception/reporting start. That is not silently substituted for the exchange's
  June 26 trading commencement; both dated facts are retained with distinct
  meanings. [issuer fund page](https://www.proshares.com/our-etfs/strategic/fb),
  [SEC shareholder data](https://www.sec.gov/Archives/edgar/data/1174610/000117461026000011/R2.htm).
- **Separation:** Meta's Class A `FB` assignment ended in 2022; this is a different
  filer, fund series/class, security, listing, and 2025 commencement (**PASS**).
  The fund assignment's end remains **UNKNOWN/open**.
- **Dated availability evidence:** the SEC filing and Cboe circular are dated
  before the exchange-trading start. This does not establish their first-public
  instants or certify an unsupported historical cutoff; those remain **UNKNOWN**.
- **OpenFIGI:** not queried in this experiment (**EMPIRICAL TEST INCONCLUSIVE**).
  A current `FB` candidate could enrich only after matching this exact fund class
  and listing; it could never reinterpret a historical Meta `FB` reference.

### 4. Twitter common stock: `TWTR` terminal lifecycle

- **Issuer/security/listing:** Twitter, Inc., CIK `0001418091`; common stock,
  par value $0.000005; `TWTR`; NYSE (**PASS**). The 2021 10-K was accepted
  2022-02-16 and reports that relationship. [2021 Form 10-K](https://www.sec.gov/Archives/edgar/data/1418091/000141809122000029/twtr-20211231.htm),
  [filing header](https://www.sec.gov/Archives/edgar/data/1418091/000141809122000029/0001418091-22-000029-index-headers.html).
- **Terminal chain:** the issuer 8-K says the merger completed **2022-10-27**,
  each outstanding share was converted into the cash right, and trading was
  suspended before the **2022-10-28** NYSE open. The NYSE Form 25 separately says
  the entire class would be removed at the opening of business on **2022-11-08**
  (**PASS**, with conversion, suspension, and formal removal stored as different
  events). [issuer 8-K](https://www.sec.gov/Archives/edgar/data/1418091/000119312522272772/d411753d8k.htm),
  [8-K filing metadata](https://www.sec.gov/Archives/edgar/data/1418091/000119312522272772/0001193125-22-272772-index.htm),
  [NYSE Form 25 exhibit](https://www.sec.gov/Archives/edgar/data/876661/000087666122000890/ruleprovisionnotice.htm).
- **Validity:** the issuer's 2013 10-K says NYSE trading as `TWTR` began on
  **2013-11-07** (**PASS**); the terminal sequence closes the listed relationship.
  [2013 Form 10-K](https://www.sec.gov/Archives/edgar/data/1418091/000095012314003031/twtr-10k_20131231.htm),
  [2013 final prospectus](https://www.sec.gov/Archives/edgar/data/1418091/000119312513431301/d564001d424b4.htm).
- **Historical availability:** the issuer 8-K was accepted 2022-10-28 20:22:36,
  after that morning's suspension. It cannot establish a pre-open information
  state. The NYSE Form 25 was accepted at 2022-10-28 08:31:19 and describes the
  suspension and planned removal. That acceptance time does **not** demonstrate
  when the filing became public. **Public availability before the 09:30 regular
  open is UNKNOWN**, so pre-open public-information eligibility is not passed.
  The exact merger effective clock time, suspension instant and first-public
  instant also remain **UNKNOWN**. The documents support the separately stated
  economic dates in retrospective research, not an invented intraday information
  ordering or an acceptance-as-publication substitution.
  [NYSE Form 25](https://www.sec.gov/Archives/edgar/data/1418091/000087666122000890/xslF25X02/primary_doc.xml).
- **OpenFIGI:** not queried (**EMPIRICAL TEST INCONCLUSIVE**). Any retired FIGI
  candidate would be enrichment only and would not establish these terminal dates.

### 5. Google/Alphabet: `GOOGL` / `GOOG` classes and issuer succession

- **Issuer/filer epochs:** Google Inc., CIK `0001288776`, before the 2015 holding-
  company reorganization; Alphabet Inc., CIK `0001652044`, afterward (**PASS**).
  CIK alone cannot join the epochs, and “same current issuer” would erase a real
  successor conversion.
- **2014 class/ticker event:** effective **2014-04-03**, existing Google Class A
  changed `GOOG` → `GOOGL`; newly distributed Google Class C used temporary
  `GOOCV` and then `GOOG`. Both were Nasdaq Global Select Market listings
  (**PASS**). [Nasdaq 2014 alert](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2014-24),
  [Google Q1 2014 10-Q](https://www.sec.gov/Archives/edgar/data/1288776/000128877614000040/goog10-qq12014.htm),
  [Nasdaq class/CUSIP FAQ](https://www.nasdaqtrader.com/content/GOOGLEfaq.pdf).
- **2015 successor/security event:** on **2015-10-02**, Google Class A and C shares
  converted one-for-one into corresponding Alphabet classes; Google shares were
  suspended after that close. Alphabet Class A `GOOGL` and Class C `GOOG` began
  trading **2015-10-05**. The CUSIPs changed for both classes (**PASS**). [Google successor-issuer 8-K](https://www.sec.gov/Archives/edgar/data/1288776/000119312515336550/d56649d8k.htm),
  [Nasdaq 2015 notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2015-156).
- **Target-period checkpoint:** Alphabet's 2021 10-K and a July 2021 8-K report
  Class A `GOOGL` and Class C `GOOG` on Nasdaq Global Select Market; Class B is
  not listed (**PASS**). Current ends remain **UNKNOWN/open**. [2021 Form 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204422000019/goog-20211231.htm),
  [July 2021 8-K](https://www.sec.gov/Archives/edgar/data/1652044/000119312521210942/d181634d8k.htm).
- **Dated availability evidence:** both Nasdaq event notices are dated before
  their respective trading-effective dates. The 2015 8-K was accepted 2015-10-02
  16:10:58, after that day's close and before the October 5 Alphabet open.
  Acceptance does not supply a first-public timestamp; historical eligibility
  requiring unavailable publication evidence remains **UNKNOWN**.
- **OpenFIGI:** not queried (**EMPIRICAL TEST INCONCLUSIVE**). Enrichment must
  preserve two classes and the Google→Alphabet issuer/security conversion; a
  current FIGI must not be used to invent either historical epoch.

### 6. Apple common stock: stable control

- **Issuer/security/listing:** Apple Inc., CIK `0000320193`; common stock;
  `AAPL`; Nasdaq (**PASS** at each inspected observation). The 2021 and 2025
  10-Ks independently report the same mapping. [2021 Form 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm),
  [2021 filing metadata](https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/0000320193-21-000105-index.htm),
  [2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm),
  [2025 filing metadata](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079-index.html).
- **Validity:** the endpoints prove dated observations, not an unbroken interval.
  Because absence of a change notice is not evidence, both complete interval bounds
  remain **UNKNOWN** and five-year continuity is **EMPIRICAL TEST INCONCLUSIVE**.
- **Historical availability:** recorded acceptance is system metadata, not a
  demonstrated public-availability boundary. The point identity observations
  support retrospective research; earlier public-information eligibility remains
  **UNKNOWN** without separate availability evidence. Backfilling the gap is not
  supported.
- **OpenFIGI:** not queried (**EMPIRICAL TEST INCONCLUSIVE**). A current identifier
  could enrich the class after reconciliation but could not close the interval.
- **Class-specific false-positive control:** a 2025 Apple Form 25 removed only its
  `0.000% Notes due 2025`, not common stock. Terminal events must join on security
  class, never CIK alone. [Apple Form 25](https://www.sec.gov/Archives/edgar/data/320193/000135445725001138/xslF25X02/primary_doc.xml).

## Required-property classification

Cells with two labels distinguish a proved assertion from a still-open part of
the property; this avoids turning a boundary PASS into a complete-interval PASS.

| Property | FB→META | META→METV ETF | later FB ETF | TWTR | GOOG/GOOGL | AAPL |
|---|---|---|---|---|---|---|
| Issuer/filer identity | PASS | PASS | PASS | PASS | PASS | PASS |
| Security/share-class identity | PASS | PASS | PASS | PASS | PASS | PASS |
| Listing identity/venue | PASS | PASS | PASS | PASS | PASS | PASS at observations |
| Ticker assignment distinguished without conflation | PASS | PASS | PASS | PASS | PASS | PASS at observations |
| Direct effective/start boundary | PASS | META start UNKNOWN; rename PASS | PASS for listing start | PASS | PASS, including issuer succession | UNKNOWN |
| Direct effective/end boundary | FB end PASS; META end UNKNOWN | META end PASS; METV end UNKNOWN | UNKNOWN/open | PASS terminal sequence | UNKNOWN/open | UNKNOWN/open |
| Dated publication/acceptance evidence; eligibility limits | Dated issuer/exchange notices; first-public instant UNKNOWN | Dated prospectus/supplement; first-public instant UNKNOWN | Dated filing/circular; first-public instant UNKNOWN | Pre-open public availability UNKNOWN; acceptance is not proof | Dated notices/filings; unsupported cutoff eligibility UNKNOWN | Acceptance observations; earlier public eligibility UNKNOWN |
| Exact evidence retention/version route | UNKNOWN | UNKNOWN | FAIL for default Cboe persistent-ledger route | UNKNOWN | UNKNOWN | UNKNOWN |
| OpenFIGI enrichment without authority | PASS for company | PASS separation; exact ETF crosswalk EMPIRICAL TEST INCONCLUSIVE | EMPIRICAL TEST INCONCLUSIVE | EMPIRICAL TEST INCONCLUSIVE | EMPIRICAL TEST INCONCLUSIVE | EMPIRICAL TEST INCONCLUSIVE |
| Deterministic after evidence retrieval | PASS | PASS for stated rename; class-name continuity manual | PASS | PASS for event sequence | PASS for class split | PASS for observations; interval remains inconclusive |
| Population-scale completeness/workload | EMPIRICAL TEST INCONCLUSIVE | EMPIRICAL TEST INCONCLUSIVE | EMPIRICAL TEST INCONCLUSIVE | EMPIRICAL TEST INCONCLUSIVE | EMPIRICAL TEST INCONCLUSIVE | EMPIRICAL TEST INCONCLUSIVE |

The retention result concerns the complete multi-source route, not a blanket
EDGAR reuse prohibition. SEC's [FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions)
expressly permits access/reuse of EDGAR public filing content, and its
[dissemination policy](https://www.sec.gov/about/privacy-information#website-dissemination)
permits copying/distribution and requests appropriate attribution. This is stronger than
the earlier access-only assessment. It does not demonstrate retrieval of every
removed version, approve all non-SEC issuer/exchange copies, or certify #31.
The earlier source-rights screen found Cboe's default terms incompatible
with a demonstrated unrestricted persistent ledger route. Facts, URLs, accessions,
hashes, and derived assertions can be retained separately from copied source
expression, but that narrower design has not been approved or tested as a #31
retained-snapshot substitute.

## Workload observations

Counts and durations are retrospective human-work estimates, not instrumented
timings, API request measurements or population extrapolations. A join means one independent
reconciliation across filer, class, listing, ticker, event, or publication time.

| Case | Source documents | Independent joins | Ambiguous/manual steps | After retrieval | Pattern reuse | Approximate burden |
|---|---:|---:|---:|---|---|---|
| FB→META | 4 | 3 | 1 | Deterministic | High: issuer filing + exchange rename | 30–45 min |
| META→METV ETF | 3 | 3 | 2 | Rename deterministic; listing start remains open | Medium-high: fund series/class + supplement | 35–60 min |
| later reused FB | 2 new + prior Meta chain | 4 | 1 | Deterministic | High for reuse once both identities exist | 30–45 min |
| TWTR | 4 | 4 | 2 | Deterministic event sequence; intraday As-Of review manual | High: issuer completion + exchange Form 25 | 60–90 min |
| GOOG/GOOGL | 5–6 | 5 | 3 | Deterministic only with issuer epochs/conversions | High but structurally richer | 90–150 min |
| AAPL control | 2 | 2 | 2 | Point observations deterministic; continuity not | Low for proving absence; high for cover extraction | 20–35 min |
| **Panel** | **about 20 core documents** | **about 21** | **about 11** | — | — | **about 4–7 focused hours after contract/source familiarization** |

The dominant workload is not parsing a cover-page tuple. It is finding a source
that actually establishes an effective boundary, reconciling it to the exact
class/listing, separating economic effect from publication and retrieval time,
and reviewing retention/version terms. Proving unchanged continuity is harder
than recording a positive change event. ETFs and terminal events cost more because
one filer may contain many classes and one lifecycle has several non-equivalent
end dates.

Automation can deterministically extract EDGAR cover tuples and series/class IDs,
index accessions/acceptance times, explicit old/new ticker clauses, exchange
effective-date clauses, and event-to-ledger joins. Manual review remains necessary
for ambiguous class continuity, successor/reorganization semantics, conflicting
dates, stale disclosure tickers, missing/publication precision, source rights,
and whether discovery coverage is complete enough to support an absence claim.

## Minimal application-owned evidence ledger (concept only)

The experiment supports a logical ledger independent of any eventual price
provider. No schema is implemented or approved here. A relationship must retain:

- typed issuer/filer identity and source namespace;
- typed security/share-class identity, including fund series/class where applicable;
- listing identity and venue, separate from the security;
- literal ticker assignment with open or evidenced effective bounds;
- event type (assignment, rename, listing commencement/transfer, conversion,
  suspension, formal removal) rather than one generic “end”;
- evidence source/accession/event identifier and the exact assertion it supports;
- source publication/acceptance precision, economic effective time, and local
  retrieval observation as separate timestamps;
- status/confidence grounded in evidence (`verified`, `candidate`, `ambiguous`,
  `unresolved`) and explicit unknown bounds;
- optional OpenFIGI composite/share-class/venue enrichment plus its retrieval
  observation, never used as historical authority; and
- parser/resolution version, raw-source reference/hash where retention is allowed,
  and later corrections without overwriting earlier observations.

This ledger is useful regardless of the price provider because provider symbols
must be downstream of a resolved historical security/listing relationship. It
also makes one resolved relationship reusable across many disclosure Events.

## Answers to the ten decision questions

1. **Can the six cases be represented without ticker conflation?** Yes. The ETF's
   2021 `META`, Meta Platforms' 2022 `META`, Meta Platforms' old `FB`, ProShares'
   2025 `FB`, and Alphabet's class-specific `GOOG`/`GOOGL` all remain separate.
2. **Fully evidenced versus open boundaries?** The requested positive transitions
   are directly evidenced for FB→META, META→METV, later-FB commencement, TWTR's
   terminal sequence, and the Alphabet class/ticker split. AAPL has only dated
   stable observations. Every case retains at least one open bound; none is a
   closed lifetime interval with an approved exact-version retention chain.
3. **Does OpenFIGI help safely?** Yes, as optional stable enrichment after
   reconciliation. The retained META/METV experiment produced distinct company
   and ETF pairs. It did not provide historical dates, and the ETF's exact current
   class/name continuity remains inconclusive.
4. **Is free historical identity solvable for a bounded Signal population?**
   **Validated PLAUSIBLE.** Positive event boundaries and class identities are
   available free for these cases. Complete discovery, retention/version rights,
   and unchanged intervals remain unresolved.
5. **Deterministic versus manual?** Structured extraction and joins become
   deterministic after retrieval. Discovery completeness, class/reorganization
   interpretation, As-Of eligibility, absence/continuity, conflicts, and rights
   review remain manual.
6. **Dominant workload?** Boundary-source discovery and reconciliation, followed
   by publication/retention review—not storage or ticker normalization.
7. **Reasonable for a solo project?** Yes for a small, event-derived population
   with reusable patterns and explicit unresolved states; no evidence supports
   building or maintaining a complete U.S. security master.
8. **Useful regardless of the market-price provider?** Yes. It prevents provider
   ticker conventions from becoming identity authority and supplies reusable,
   auditable joins for every provider candidate.
9. **Status recommendation?** Move from overall **UNRESOLVED** to **validated
   PLAUSIBLE for a bounded population only**. Keep complete historical identity
   and #31 production readiness unresolved. It is not a demonstrated practical
   blocker and does not change readiness.
10. **Single smallest next action:** take **20 distinct security/date references
    from an already-retained bounded set of official Signal disclosure rows** and
    time the same evidence worksheet: auto-resolved count, manual minutes,
    unresolved reasons, source documents, and reusable-pattern hits. This tests
    actual population mix without implementing a schema, integrating a provider,
    or pretending the six deliberately chosen cases establish scale.

No additional case was added. The required Google/Alphabet case already exposes
the materially different ticker reassignment across classes plus successor-issuer
conversion failure mode.
