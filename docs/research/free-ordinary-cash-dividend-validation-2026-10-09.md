# Free ordinary-cash-dividend component: bounded validation

Observation date: **2026-10-09**. Research/validation only. No provider was
selected or integrated, no production code, issue, capability or readiness state
was changed, and no Git command was run. This research note is the only retained
repository artifact.

## Decision

**A defensible free component is not established for the Signal population.**
The bounded panel shows that free sources can reconstruct positive events and can
occasionally establish a true no-dividend interval. The route still fails the
approved contract because the only observed near-complete event ledgers cannot be
used as retainable, versioned inputs under their published terms, and the
permitted primary-source chain does not provide complete discovery plus explicit
event ex-dates.

The strongest permissible evidence chain is:

1. original EDGAR/issuer declarations for cash amount, event type and then-current
   share basis;
2. authoritative exchange material for ex-date meaning and exceptional dates;
3. separately dated historical security/listing evidence; and
4. application-owned retrieval/version records only where exact-byte retention is
   permitted.

That chain is strong for individual events. It is not a complete ordinary-cash-
dividend ledger. Missing records remain **UNKNOWN**, except where an attributable
source explicitly asserts the negative for the security and period.

## Approved boundary and validation method

The validation first inspected [#31](https://github.com/AviSharma01/signal-workspace/issues/31),
the [provider-neutral conformance contract](../market-data-conformance.md), approved
[#26 / V2 section 6](../specs/signal-v2.md#6-benchmark-and-return-semantics), the
[corporate-action screen](free-corporate-action-component-screen-2026-10-08.md),
[identity screen](historical-security-identity-screen-2026-10-09.md), and
[calendar validation](exchange-session-calendar-validation-2026-10-09.md).

The then-current synthesis draft was also a historical input, not an independent expectation; the final synthesis is downstream of this validation.

The unchanged requirement is an original per-share cash amount, ex-date,
currency, historically resolved security/listing identity, provenance, retained
observed versions, and evidence that distinguishes no action from insufficient
evidence. Adjusted-price reconstruction is excluded.

The main panel covers **2021-01-01 through 2025-12-31**: five complete calendar
years, long enough for twenty quarterly cycles. It includes SPY, AAPL, NVDA,
TSLA as an explicit nonpayer, COST with a special distribution, and TWTR as a
terminal-identity control. Partial 2026 observations were inspected only to
identify the remaining full-contract gap; they are not used to claim a complete
2026 panel. The repository does not contain a certified complete historical
Signal population from which to draw a coverage sample, so these are required
methodological controls, not evidence of population-wide coverage.

Expectations were not taken from the candidate observation alone. Issuer histories,
original EDGAR/issuer declarations and SEC-filed annual reports supplied the
independent or partially independent controls described below. When the original
records were only sampled rather than exhaustively reconciled, completeness is
**EMPIRICAL TEST INCONCLUSIVE**, not PASS.

Classification: **PASS** = directly supported for the stated case/scope;
**FAIL** = observed incompatibility; **UNKNOWN** = required evidence was not
available; **EMPIRICAL TEST INCONCLUSIVE** = bounded testing did not establish the
property. No panel PASS is population-wide certification.

## Bounded observations

| Case | Expected events, 2021–2025 | Observed reconciliation | Decision |
|---|---:|---|---|
| U.S. SPY | 20 quarterly distributions | State Street's U.S. historical-distributions XLSX contained exactly 20 SPY rows, each with CUSIP `78462F103`, ex-date, record date, payable date and cash distribution. Separate short- and long-term capital-gain columns were blank or zero for those rows. The product page identifies NYSE Arca, SPY and USD. The SEC-filed 2025 annual report independently says the Trust distributes quarterly and reports per-unit distributions for each fiscal year 2021–2025. | Fact-level ledger **PASS**; corrections **UNKNOWN**; exact-byte retained-input route **FAIL** under the page's copying restriction. |
| AAPL | 20 regular cash dividends | Apple's issuer history listed exactly 20, labeled regular cash and not split-adjusted. A Nasdaq-hosted dividend response also returned 20 with explicit USD/ex-date fields and matching amounts/record/pay dates. Selected original declarations were reconciled. | Amount/share basis **PASS**; exhaustive permitted-source discovery **EMPIRICAL TEST INCONCLUSIVE**; authoritative retainable ex-date route **FAIL**. |
| NVDA | 20 regular cash dividends | The Nasdaq-hosted response returned 20. Original NVIDIA records confirm sampled events and the share-basis transitions: $0.16 before the 2021 4:1 split, $0.04 after it, and $0.01 after the 2024 10:1 split. Only the June 2024 issuer FAQ supplied an explicit tested ex-date. | Original amount/share basis **PASS**; exhaustive permitted-source discovery **EMPIRICAL TEST INCONCLUSIVE**; multi-year authoritative retainable ex-date route **FAIL**. |
| COST | 20 regular + 1 special cash dividend | The Nasdaq-hosted response returned 21 rows. Original filings support sampled regular declarations and the $15 special declared in December 2023. Costco's current history is supplied by Mergent and disclaims direct maintenance. | Original amount/type **PASS** for sampled events; exhaustive permitted-source discovery **EMPIRICAL TEST INCONCLUSIVE**; authoritative retainable ex-date route **FAIL**. |
| TSLA | 0 ordinary cash dividends | Tesla's 2025 Form 10-K identifies common stock / TSLA / Nasdaq and explicitly says it has never declared or paid cash dividends; an earlier annual report independently made the same assertion. | No ordinary cash dividend through 2025-12-31 **PASS**. |
| TWTR terminal control | No count assumed | Twitter's 2021 Form 10-K states that it had never declared or paid cash dividends and identifies common stock / TWTR / NYSE. The 2022 8-K establishes cancellation on 2022-10-27 and suspension before the 2022-10-28 open. | Historical identity/terminal join **PASS**; full 2022 no-dividend interval **EMPIRICAL TEST INCONCLUSIVE**. |

### Exact controls

| Control | Exact source terms | Result |
|---|---|---|
| AAPL declared 2024-05-02 | $0.25 per common share; record 2024-05-13; payable 2024-05-16. Apple's history says amounts are not split-adjusted. The rejected Nasdaq response showed ex-date 2024-05-10 and USD. | Original amount/basis **PASS**; issuer source omits ex-date; the only observed explicit ex-date was not a contract-usable retained input. [Apple history](https://investor.apple.com/dividend-history/default.aspx), [EDGAR filing directory](https://www.sec.gov/Archives/edgar/data/320193/000032019324000067/). |
| NVDA declared 2021-05-26 | $0.16 per then-current share; record 2021-06-10; payable 2021-07-01. | Original basis **PASS**; it must not be retrospectively divided by the later 4:1 and 10:1 splits. The original omits ex-date. [Original EDGAR exhibit](https://www.sec.gov/Archives/edgar/data/1045810/000104581021000063/q1fy22pr.htm), [2021 split FAQ](https://investor.nvidia.com/files/doc_downloads/doc_faq/06/21/NVIDIA-2021-Stock-Split-FAQ.pdf). |
| NVDA declared 2024-05-22 | Ex-date 2024-06-11; $0.01 per post-10:1-split share; payable 2024-06-28. | The only tested positive equity event with amount, basis and ex-date explicit in one issuer document: fact-level **PASS**. It does not prove the other nineteen events or retained-version rights. [Issuer FAQ](https://investor.nvidia.com/files/doc_downloads/2024/06/nvidia-2024-stock-split_faq_investors.pdf), [original release](https://investor.nvidia.com/news/press-release-details/2024/NVIDIA-Announces-Financial-Results-for-First-Quarter-Fiscal-2025/). |
| COST special declared 2023-12-13 | $15 per common share; record 2023-12-28; payable 2024-01-12; approximately $6.7 billion aggregate. The rejected Nasdaq response showed ex-date 2023-12-27 and USD. | Amount/security/special type **PASS**. The original omits ex-date, and deriving it from settlement rules would not be event-specific exchange evidence. [Original EDGAR exhibit](https://www.sec.gov/Archives/edgar/data/909832/000090983223000062/costex9918-k121423.htm). |
| TSLA negative interval | The 2025 Form 10-K says Tesla has never declared or paid cash dividends and identifies the listed security. | No-dividend through 2025 **PASS** because the source asserts the negative; this rule cannot be transferred to other missing records. [2025 Form 10-K](https://www.sec.gov/Archives/edgar/data/1318605/000162828026003952/tsla-20251231.htm), [filing index](https://www.sec.gov/Archives/edgar/data/1318605/0001628280-26-003952-index.htm). |

Currency is independently supportable as USD in these controls from explicit
fields or the U.S. filing/listing and dollar-denominated declaration context. A
bare dollar sign without that context would not pass.

### Isolated observation manifest

No raw source snapshot was added to the repository because the relevant terms
are restrictive or unresolved. These observations therefore do **not** satisfy
#31 offline replay.

| Observation | Local retrieval | Derived evidence retained here |
|---|---|---|
| State Street U.S. SPDR Historical Distributions XLSX | 2026-10-09 16:29:09 +05:30; 581,242 bytes; SHA-256 `b162dd17027d1128f2209e312b0f634960daa78319dafe0ab821ab0b7e77ce23` | SPY count, schema and selected facts only. Raw workbook was not committed. |
| Nasdaq-hosted dividend responses for AAPL, NVDA and COST | 2026-10-09 16:21–16:22 +05:30 | Counts and selected reconciliations only. Raw responses were not committed and are rejected as component inputs under Nasdaq's terms. |

## Ten required properties by case

Abbreviations: P = PASS, F = FAIL, U = UNKNOWN, E = EMPIRICAL TEST
INCONCLUSIVE, and — = not applicable.

| Property | AAPL | NVDA | U.S. SPY | COST | TSLA no-event | TWTR terminal |
|---|---|---|---|---|---|---|
| 1. Every expected ordinary cash dividend discovered | E | E | P for the bounded sponsor ledger | E | P | E |
| 2. Original amount/share basis preserved | P | P with originals | P | P for sampled originals | — | — |
| 3. Ex-date explicit and authoritative | F for usable route | one event P; multi-year F | P | F for usable route | — | — |
| 4. Currency explicit or independently supportable | P | P | P | P | — | — |
| 5. Safe historical-security join | P for sampled originals | P for sampled originals | P | P for sampled originals | P | P |
| 6. Corrections/amendments observable | U | U | U | U | U | U |
| 7. Exact observed records/versions retainable | F for required issuer/Nasdaq route; SEC reuse P, version coverage U | F for required issuer/Nasdaq route; SEC reuse P, version coverage U | F under observed State Street terms | F for required issuer/Mergent/Nasdaq route; SEC reuse P, version coverage U | SEC reuse P; retained-version/replay coverage U | SEC reuse P; retained-version/replay coverage U |
| 8. Missing record can mean “no dividend” | F | F | F | F | P only because the filing states the negative | F |
| 9. Measured solo extraction workload | E | E | E | E | E | E |
| 10. Zero monetary access cost | P for reads, not a complete route | P for reads, not a complete route | P for reading; retained route F | P for reads, not a complete route | P | P |

No case passed all ten properties. U.S. SPY was fully reconstructed at the
fact level for 2021–2025 but fails exact retained-input rights and has no observed
revision chain. The June 2024 NVDA event was fully reconstructed at the fact
level. TSLA supplied a defensible no-dividend conclusion, but a complete retained-version/revision/replay package was not established.
SEC public-filing reuse permission is distinguished below from that evidence gap.

## Source-route findings

### EDGAR originals and issuer disclosures

This is the strongest semantic spine and an incomplete discovery mechanism.
Original releases preserve the declared amount and event share basis and often
name the issuer, class and ticker. NVIDIA demonstrates why originals matter: its
later 10-K retrospectively adjusts share/per-share figures for the 2024 split,
whereas the 2021 original preserves $0.16 on that event's basis. [NVIDIA 2025
10-K](https://www.sec.gov/Archives/edgar/data/1045810/000104581025000023/nvda-20250126.htm).

Routine dividends are not a universal mandatory 8-K inventory, SEC companyfacts
is not a corporate-action ledger, and current issuer tables can be overwritten
without exposing every prior version. Absence in EDGAR or an issuer search is
therefore **UNKNOWN**.

Free access is not sufficient retention permission. Apple restricts copying,
mirroring and automated acquisition; Costco's site terms restrict automated
extraction and most copying; NVIDIA grants limited personal use and includes
termination restrictions. **2026-10-15 clarification:** SEC explicitly permits
reuse of EDGAR public filing content; its dissemination policy permits copying/
distribution and requests appropriate attribution;
the earlier access-only assessment was incomplete. This permission does not
establish a complete dividend inventory or recovery of removed versions, and
does not apply to non-SEC issuer-site copies. [SEC reuse FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions),
[dissemination policy](https://www.sec.gov/about/privacy-information#website-dissemination). [Apple
terms](https://www.apple.com/legal/internet-services/terms/site.html), [Costco
terms](https://www.costco.com/f/-/terms-and-conditions-of-use), [NVIDIA
terms](https://www.nvidia.com/en-us/about-nvidia/terms-of-service/), [17 U.S.C.
section 105](https://www.copyright.gov/title17/92chap1.html).

### Nasdaq structured observation and exchange dates

The Nasdaq-hosted response was technically attractive: ex/effective date, cash
amount, declaration date, record date, payment date and currency. Nasdaq's market-
activity FAQ says historical dividend information is not split-adjusted, and the
observed NVDA rows empirically preserved the $0.16 → $0.04 → $0.01 share-basis
transitions. The same bounded responses matched the five-year issuer counts for
AAPL and COST.

It is nevertheless a **FAIL** as a Signal component. Nasdaq describes the public
history as aggregated, warns that special and regular dividends may be combined,
and its current website terms prohibit capturing or compiling site content for
data-analysis software, automated/manual extraction, copying and later storage
without written permission. The endpoint is not a documented free historical
Daily List entitlement. [Nasdaq market-activity FAQ](https://www.nasdaq.com/market-activity),
[Nasdaq legal terms](https://www.nasdaq.com/legal), [commercial Daily List](https://www.nasdaq.com/products/data/equities/corporate-action-solutions).

Nasdaq Rule 11140 is authoritative about mechanics: before T+1, the normal ex-date
was generally the business day before record date; after the 2024-05-28 transition,
it is generally the record date. Large and specially designated distributions
are exceptions. A rule does not turn an issuer record date into an observed,
event-specific ex-date unless complete exception coverage is also proven.
[2024 issuer alert](https://listingcenter.nasdaq.com/assets/RuleBook/Nasdaq/rules/Issuer_Alert_2024-001.pdf),
[Rule 11140](https://listingcenter.nasdaq.com/rulebook/nasdaq/rules/Nasdaq%20Equity%2011),
[free exception page](https://www.nasdaqtrader.com/Trader.aspx?id=nasdaq-ex-date).

### U.S. SPY and State Street

State Street's current U.S. workbook is fact-complete for the bounded SPY panel.
Its product page also identifies the historical security/listing and base/trading
currency. The SEC-filed 2025 annual report independently supports quarterly
distribution cadence and fiscal-year per-unit totals for 2021–2025. [U.S.
distribution page](https://www.ssga.com/us/en/institutional/resources/documents/etf-dividend-distributions),
[SPY product page](https://www.ssga.com/us/en/institutional/etfs/state-street-spdr-sp-500-etf-trust-spy),
[SEC-filed 2025 annual report](https://www.sec.gov/Archives/edgar/data/884394/000119312525297563/d18808dn30d.htm).

This still fails #31 because the distribution and product pages state that the
whole or any part of the work may not be reproduced, copied or transmitted without
express written consent. No version archive or correction chain was exposed.
The sponsor evidence can be read and manually validated for free; it cannot yet
be retained and replayed as required.

### Corrections, absence and workload

- **Corrections:** no changed dividend record was observed. SEC can expose a new
  filing or amendment, but current issuer/exchange tables need not expose overwritten
  values. This property is **UNKNOWN** everywhere in the panel.
- **Absence:** a source can support zero only when it expressly covers the security,
  action type and period and exposes finality/correction semantics. TSLA supplies
  the first part. Empty APIs, missing 8-Ks, blank exception pages and absent issuer
  search hits mean **UNKNOWN**.
- **Workload:** even this six-case panel required current histories, original
  declarations, split-basis checks, date-rule/exception checks, currency support,
  identity evidence and source-terms review. No timed population run was performed,
  so workload remains **EMPIRICAL TEST INCONCLUSIVE**. Event-by-event manual
  reconstruction is unlikely to be reasonable for a solo project without a
  retainable structured inventory.

## Answers to the decision questions

1. **Realistically achievable?** A partial positive-event evidence component is;
   a contract-complete free component for the Signal population is not established.
2. **Strongest combination?** EDGAR/issuer originals + authoritative exchange
   event/rule evidence + dated identity evidence. State Street is the strongest
   SPY fact source but requires retention permission.
3. **Fully reconstructed samples?** U.S. SPY 2021–2025 at fact level, the June
   2024 NVDA event, and TSLA's no-dividend interval. None passes all ten contract
   properties because retention/revision evidence remains blocked or unknown.
4. **Where did discovery or semantics fail?** Permitted sources lack a universal
   event inventory and most issuer originals omit ex-date. The two near-complete
   structured histories are unusable as retained inputs under published terms.
5. **Can “no dividend” be established?** Yes, narrowly, when an attributable
   filing explicitly states the negative for the security/period, as Tesla does,
   or when a future source explicitly certifies complete no-action coverage.
6. **What blocks complete 2021–2026 coverage?** Retainable complete discovery,
   event-specific ex-dates including exceptions, observed corrections/versions,
   exact-byte rights, full partial-2026 finality, and measured population-scale
   identity/extraction workload.
7. **Reasonable solo workload?** Individual events are manageable; population
   coverage is not shown reasonable and is likely too costly without a structured,
   retainable inventory.
8. **Should broad dividend-source research stop?** **Yes.** Stop generic provider
   shopping. The remaining question is rights/coverage for a named authoritative
   dataset, not another undocumented feed.
9. **Single smallest next action:** ask State Street for written permission to
   automate, indefinitely retain and version the exact U.S. **SPDR Historical
   Distributions XLSX** for personal/noncommercial Signal research, including old
   observed versions and derived facts. A refusal rejects the strongest free SPY
   route; a grant enables one tiny U.S.-SPY replay test. It does not alter #31.
