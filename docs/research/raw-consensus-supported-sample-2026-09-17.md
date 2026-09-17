# Raw Consensus supported-sample evidence gate

Observed 2026-09-17 UTC. Research for [Establish supported-sample computability of Raw Consensus](https://github.com/AviSharma01/signal-workspace/issues/19), under the [recorded bounded plan](https://github.com/AviSharma01/signal-workspace/issues/19#issuecomment-5709754207). This is evidence, not an approved window, methodology change, or population-coverage certification.

## Result and handoff

**Unsupported within the bounded investigation.** Neither selected filing acquired supported original-publication availability with calendar/timezone meaning and historical artifact/version lineage. Thus no eligible target sample or contextual cutoff was established. Raw Consensus, Other Reporting Members, count distributions, zero-peer rates, and unresolved-membership rates remain **unavailable**, not observed zeros. No lookback lengths were frozen or calculated; no peer search began.

[Choose primary and sensitivity Raw Consensus windows](https://github.com/AviSharma01/signal-workspace/issues/15) remains **evidence-blocked even if this research ticket is closed**. Missing prerequisites are target-specific original publication evidence, its calendar meaning and version association, historically supported occurrence/member/security interpretation, and correction-aware evidence at the derived pre-session cutoff. Those must precede a bounded peer search covering any proposed illustrative lengths. Completion of this investigation does not authorize a default, broader ingestion, another search, prospective collection, or relaxation of the approved semantics.

The result establishes inability to support computability through this particular probe, not that all historical evidence is impossible to obtain. Present-day document access is insufficient under [Define Event, Watch Event eligibility, and point-in-time semantics](https://github.com/AviSharma01/signal-workspace/issues/6) and [Define Raw Consensus counting and grouping semantics](https://github.com/AviSharma01/signal-workspace/issues/12).

## Frozen scope and stop rule

Before acquiring external source evidence, the parent recorded this plan: House-only, nominal filing year 2025; one official annual index; select the first two distinct `P`-type DocIDs in ascending numeric order, without reference to member, security, transaction direction, outcomes, or counts. Candidate sources were the official House disclosure portal/search, that index, its selected PTR URLs, and House Ethics guidance. Ceiling: eight request attempts, one archive, two PDFs, up to five documentation responses, and 30 minutes. Stop on unsupported prerequisite evidence; no replacement candidates or automatic peer phase.

Eight externally oriented operations were counted conservatively, including two screenshot operations against already opened PDFs. Acquisition and inspection took less than ten minutes. No retry, authentication, aggregator request, Senate request, market-data request, or application-data query occurred. No returns, prices, significance, predictive/anomaly performance, or other outcomes were inspected.

## New observations and request log

| Operation | URL / action | Observed result and scope |
|---|---|---|
| 1 | [House disclosure landing page](https://disclosures-clerk.house.gov/FinancialDisclosure) | Web tool returned HTML navigation/contact material; no selected-filing publication ledger in returned content. HTTP status not exposed by this tool. |
| 2 | [House search](https://disclosures-clerk.house.gov/FinancialDisclosure/ViewSearch) | Web tool returned search controls, Filing Year, and use restrictions; no historical publication fields for selected records. No search submitted. HTTP status not exposed. |
| 3 | [2025FD.ZIP](https://disclosures-clerk.house.gov/public_disc/financial-pdfs/2025FD.ZIP) | Direct GET: HTTP 200, 106,005 bytes. Archive contains `2025FD.txt` and `2025FD.xml`. Selection used the TXT representation only. |
| 4 | [Selected Self PTR](https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/8220731.pdf) | Web tool identified a two-page PDF, with zero extracted text lines; HTTP status and raw PDF bytes not exposed. No transaction content validated. |
| 5 | [Selected Bilirakis PTR](https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/8220747.pdf) | Web tool identified a two-page PDF, with zero extracted text lines; HTTP status and raw PDF bytes not exposed. No transaction content validated. |
| 6 | [House Ethics amendment guidance](https://ethics.house.gov/manual/filing-deadlines-committee-review-and-amendments/) | Returned official guidance permits amendment by letter rather than a complete replacement form and says originals and amendments become public. It supplies no selected-target publication/version history. |
| 7 | First-page screenshot of selected Self PDF | Returned a screenshot reference without a usable image payload in the orchestration output. No visual reading claimed. |
| 8 | First-page screenshot of selected Bilirakis PDF | Same limitation. Counted toward ceiling; no follow-up attempt. |

The archive response reported `Date: Thu, 17 Sep 2026 06:08:07 GMT`, `Last-Modified: Wed, 16 Sep 2026 13:00:40 GMT`, and ETag `"51be7360db45dd1:0"`. These describe the retrieved archive representation; they do not establish first publication of its constituent filings. Its SHA-256 is `a45fefec8559f56feeaa1087c85d9d5f6e4507d4f399292f8339b485b102cd5f`. Temporary bytes and headers were captured at `/tmp/consensus-house-2025FD.ZIP` and `/tmp/consensus-house-index.headers`; those temporary files are not durable published assets. This report retains the hash, selection procedure, selected raw index fields, and limits; a later live download may differ.

The TXT header is `Prefix, Last, First, Suffix, FilingType, StateDst, Year, FilingDate, DocID` (tab-separated). Selected raw rows:

| Prefix | Last | First | Suffix | FilingType | StateDst | Year | FilingDate | DocID |
|---|---|---|---|---|---|---|---|---|
| Hon. | Self | Keith Alan | empty | P | TX03 | 2025 | 1/23/2025 | 8220731 |
| Hon. | Bilirakis | Gus M. | empty | P | FL12 | 2025 | 2/6/2025 | 8220747 |

These are two selected **filing candidates**, not two established transaction Events. No statement is made about their transaction counts, instruments, or eligibility. Source field `FilingDate` was preserved as filing metadata, not converted to publication dates.

## Prerequisite assessment

| Requirement | Assessment within this sample |
|---|---|
| Original public timestamp/date and calendar meaning | Unknown/unverified for both filing candidates. Index filing dates and current retrieval do not supply the required original publication evidence. |
| Official retained artifact/version provenance | Partial current provenance only: official index bytes hashed; selected official PDF URLs recognized by web tool. PDF byte hashes, retained historical versions and links to original publication remain unverified. |
| Transaction-occurrence identity and multiplicity | Not established: no usable transaction extraction or visual validation; filing DocID is not an occurrence identifier. |
| Reporting-member identity at required historical boundary | Index names/districts observed; historical identity and occurrence attribution not independently established. |
| Historically resolved security identity | Not established; no security mappings or current-ticker substitutions attempted. |
| Correction-aware state strictly before target session open | Not established. General amendment guidance is not a selected-target correction ledger; original publication and hence derived cutoff are missing. |
| Peer scope and completeness over longest lookback | Not assessed: initial target gate failed; peer acquisition never started. |

The earliest gate failed through absent support, not affirmative evidence that the filings were unpublished or invalid. Later gates were not forced. A missing parse is an acquisition/inspection limitation and does not prove the PDF itself lacks publication evidence. General guidance that amendments are public does not establish their timing, linkage, withdrawal status, or exhaustive availability before a historical cutoff.

## Reproducibility and limitations

Selection can be reproduced from bytes matching the hash with Python standard libraries:

```python
import csv, hashlib, io, zipfile

raw = open('/tmp/consensus-house-2025FD.ZIP', 'rb').read()
assert hashlib.sha256(raw).hexdigest() == (
    'a45fefec8559f56feeaa1087c85d9d5f6e4507d4f399292f8339b485b102cd5f'
)
with zipfile.ZipFile(io.BytesIO(raw)) as archive:
    rows = csv.DictReader(io.StringIO(
        archive.read('2025FD.txt').decode('utf-8-sig')), delimiter='\t')
    ordered = sorted((r for r in rows if r['FilingType'] == 'P'),
                     key=lambda r: int(r['DocID']))
seen, selected = set(), []
for row in ordered:
    if row['DocID'] not in seen:
        selected.append(row)
        seen.add(row['DocID'])
    if len(selected) == 2:
        break
print(selected)
```

This deterministic selection avoids outcome/count-driven replacement but remains a small convenience probe. It does not represent House years generally, Senate disclosures, amendments, weekend publication, exact-open boundaries, date-only start crossings, or the intended Congressional population. No Event-level exclusion denominator exists here: reporting an eligibility percentage over two filings would conflate filings with occurrences. No target admission is supported; that is not a measured population failure rate.

The earlier [local-table feasibility findings](https://github.com/AviSharma01/signal-workspace/issues/15#issuecomment-5704766798), [disclosure-source research](disclosure-source-evidence-2026-09-15.md), and [House bulk research](kadoa-house-bulk-evidence-2026-09-15.md) informed source choice. Their database measurements and external observations were not re-audited. This run used a new archive with a different hash, not their earlier snapshot. The developer's prior outcome-exposure statement remains a qualified recollection, not a project-wide audited claim. Research completion supports the evidence-blocked handoff only.
