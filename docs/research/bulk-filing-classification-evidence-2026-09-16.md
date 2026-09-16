# Bulk filing classification evidence

Checked **2026-09-16 (UTC)** for [Establish evidence for bulk filing classification](https://github.com/AviSharma01/signal-workspace/issues/7). Research evidence and a bounded measurement plan; no threshold, passive classification, source selection, or implementation approval.

## Result

Filing size is measurable, but the available evidence does not validate **>=15 distinct tickers as a proxy for passive/background behavior**. A small convenience sample crosses this cutoff; this establishes neither population prevalence nor predictive accuracy. An official House example describes a deliberate portfolio divestment: portfolio-wide and intentional can coexist. Advisor-managed accounts also generate reportable transactions. The downstream decision must distinguish size, decision maker, investment intent, and independence instead of collapsing them into one label.

## Evidence inventory before measurement

At checkout `8c120b9`, the repository has [reported historical characteristics](../data/disclosure-characteristics.md), three research notes, and a local `server/signal.db`. The database was not queried: this session did not establish its source snapshot or occurrence lineage, so it cannot substantiate the old observations. The old 130 rows/127 tickers are a **member-month** observation; 1,236 rows/433 tickers span **five months**. Neither is a filing-size distribution. Missing original capture/query prevents reproduction of these or the old dedupe collapse.

The previous [Kadoa/House research](kadoa-house-bulk-evidence-2026-09-15.md) identifies two small public JSON samples at provider commit `bfd74fa9e2ec3ca45e8c89e046d9bed1c0903ca7`. Retained copies existed in `/private/tmp` before acquisition. This session inspected them, then fetched only the same two pinned files through GitHub to verify byte equality. No broader feed acquisition occurred. These are aggregator raw responses, not official raw disclosures. Their original local retrieval times were not inferred from file modification times. Provider IDs remain unverified official occurrence identities.

| Sample / pinned source | Bytes | SHA-256 |
|---|---:|---|
| [Adam Smith](https://github.com/kadoa-org/congress-trading-monitor/blob/bfd74fa9e2ec3ca45e8c89e046d9bed1c0903ca7/public/data/filer/house_adam_smith.json) | 14,628 | `d6c849262d71d22dfed4c43f93086d249142c111024cfc34fd68be767af96fbf` |
| [Ron L Wyden](https://github.com/kadoa-org/congress-trading-monitor/blob/bfd74fa9e2ec3ca45e8c89e046d9bed1c0903ca7/public/data/filer/senate_ronl_wyden.json) | 259,487 | `c57fe5522d44e4e908e0299a75c5dc0a33dd9e1311cd15d441156ad783788b3f` |

The retained House annual ZIP described in the prior note is an index, not transaction rows. It cannot yield filing sizes without individual artifacts. The [official Smith PDF](https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20030868.pdf) was readable through the web tool this session; its extracted text was inspected, not archived as a new official corpus. Senate official artifact correspondence remains unverified. Public GitHub access requires no purchased feed; House downloads require respecting portal conditions; Senate access/acknowledgment and artifact retrieval must be validated before a larger sample. Previous terms/retention and completeness caveats remain unresolved. No production data were changed.

## Exploratory measurements: aggregator groups only

Group by exact `(source_id, filing_id)` within each pinned response. Count every JSON array occurrence, without dedupe; count distinct nonblank **literal provider ticker strings**, with no alias resolution or ticker normalization. This is not a count of historically resolved securities or officially verified Events. Null/blank tickers contribute rows but not tickers. All sampled provider rows say PTR; this is not independent form validation. Neither file was filtered by year, equity eligibility, or historical availability, so this is not the primary Analysis cohort.

| Sample | Rows | Provider filing groups | Missing ticker rows | Distinct ticker count : number of groups |
|---|---:|---:|---:|---|
| Smith | 18 | 1 | 0 | 18:1 |
| Wyden | 303 | 26 | 42 | 0:4, 1:6, 2:2, 3:4, 5:1, 10:1, 13:2, 15:1, 18:2, 24:1, 25:1, 26:1 |

Wyden row-count distribution (`rows:groups`): **1:5, 2:3, 3:2, 4:3, 6:1, 7:1, 10:1, 13:1, 14:3, 20:2, 29:1, 39:2, 49:1**. Smith has one 18-row group. These distributions are conditional on two previously selected convenience files, with incomplete history and unverified extraction coverage; pooling them as population estimates would mislead.

| Candidate distinct ticker cutoff | Smith groups / rows in groups | Wyden groups / rows in groups |
|---|---:|---:|
| >=10 | 1 / 18 | 9 / 237 |
| >=14 | 1 / 18 | 6 / 196 |
| >=15 | 1 / 18 | 6 / 196 |
| >=16 | 1 / 18 | 5 / 167 |
| >=20 | 0 / 0 | 3 / 127 |

The one-step change from 15 to 16 changes one Wyden group containing 29 provider rows. Missing tickers and unresolved alias/share-class identity can also change membership. No evaluated labels of passive behavior exist here, so precision, recall, false-positive rates, and an optimal threshold are **unknown**. Counts above measure sensitivity of a convenience sample, not suitability of the cutoff.

### Reproduction

Fetch only the two pinned source links' contents using the command below (substitute the two filer names from the table); preserve bytes and verify hashes before running Python. This reproduces aggregator measurements, not official verification. `cmp` found the new pinned downloads byte-identical to both retained copies in this session.

```sh
gh api 'repos/kadoa-org/congress-trading-monitor/contents/public/data/filer/house_adam_smith.json?ref=bfd74fa9e2ec3ca45e8c89e046d9bed1c0903ca7' -H 'Accept: application/vnd.github.raw+json' > house_adam_smith.json
```

```python
import collections, hashlib, json
from pathlib import Path
for name in ('house_adam_smith', 'senate_ronl_wyden'):
    b = Path(name + '.json').read_bytes()
    rows = json.loads(b)['trades']
    groups = collections.defaultdict(list)
    for row in rows:
        groups[(row['source_id'], row['filing_id'])].append(row)
    counts = [(len(g), len({r['ticker'] for r in g
                           if r['ticker'] and r['ticker'].strip()}))
              for g in groups.values()]
    print(name, len(b), hashlib.sha256(b).hexdigest())
    print('rows/groups/missing', len(rows), len(groups),
          sum(not r['ticker'] or not r['ticker'].strip() for r in rows))
    print('row histogram', sorted(collections.Counter(n for n, u in counts).items()))
    print('ticker histogram', sorted(collections.Counter(u for n, u in counts).items()))
    print('form labels', collections.Counter(r['filing_type'] for r in rows))
    for cutoff in (10, 14, 15, 16, 20):
        print(cutoff, sum(u >= cutoff for n, u in counts),
              sum(n for n, u in counts if u >= cutoff))
```

## Primary-source interpretation and limits

- The [Senate ethics FAQ](https://www.ethics.senate.gov/public/index.cfm/ethics-faqs) explicitly describes independently advisor-managed, preset portfolios in separately managed accounts. Underlying assets and qualifying transactions still require reporting; filer responsibility continues even when the filer does not make investment decisions. **Inference:** many rows can reflect delegated management, but row count cannot identify who decided or whether the manager acted passively.
- The [Senate disclosure FAQ](https://www.ethics.senate.gov/public/index.cfm/financialdisclosure) treats qualifying dividend reinvestments as purchases, distinguishes excepted fund transactions from PTR reporting, and explains annual PTR summaries. **Inference:** repetition can reflect reinvestment or repeated presentation, and the reporting population is selected by disclosure rules. A reported transaction is not necessarily a new investment thesis; an annual summary is not automatically a newly disclosed occurrence.
- The [House disclosure page](https://ethics.house.gov/financial-disclosure/) describes transaction notification/deadline rules. **Inference:** filing batches can reflect reporting workflow and notification timing rather than a single investment decision. No reviewed official guidance defines a 15-ticker passive threshold.
- In [Smith's official filing 20030868](https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2025/20030868.pdf), the source describes spouse-owned inherited IRA securities and a choice to divest all stocks. The provider sample contains 18 different ticker strings in that group. This is evidence of a stated portfolio divestment, not proof of passive management, informed trading, or lack of information. The previously checked missing aggregator comment demonstrates why official context matters. This example supplies no historical public-availability evidence.

Other **hypotheses for future validation**, not measured conclusions: rebalancing, tax/cash needs, multiple owners/accounts, split executions, corporate actions, amendments, or parser duplication can inflate or repeat rows. Repeated tickers do not establish repeated holdings, remaining positions, or unchanged strategy. Annual asset schedules describe holdings under their own reporting rules and dates; PTRs are transaction reports. Do not infer a complete portfolio or net position from these samples.

## Bounded next measurement plan

This plan is proposed research design, not approved cohort methodology or authorization for a full acquisition.

1. **Declare the population first.** Use approved both-chamber/2021–2025 plus 2026 coverage goals, but begin with a capped pilot: at most 24 official filing artifacts, separately stratified by chamber and small/near-cutoff/large provider groups (four per cell where available). Include 14/15/16-ticker examples where feasible. Choose deterministically from a frozen inventory without inspecting returns. Explicitly report missing cells and selection bias; this pilot cannot estimate population rates.
2. **Inventory access before retrieval.** Record candidate locators, chamber/year/form, pinned provider snapshot hashes, official portal conditions, obtainable versions, publication evidence, extraction capability, and missing access. Stop at the cap or an access/provenance blocker. Do not compensate for missing official data by relabeling aggregator measurements as verified. Full minimum-history coverage requires a separately scoped acquisition/reconciliation effort.
3. **Preserve identities.** Retain exact official bytes and retrieval metadata with hash, source filing identity, artifact version and retrieval observation separately. Extract rows with page/row anchors, method/version and status. Preserve identical row occurrences. Keep original/amendment artifacts and uncertain links separate; dedupe neither by values nor URLs alone. Verified correspondence, not provider `_tN`, establishes shared occurrence identity, per [approved identity semantics](https://github.com/AviSharma01/signal-workspace/issues/5#issuecomment-5696330933).
4. **Measure two layers.** Report all source row occurrences, interpretable in-scope equity occurrences, missing/ambiguous fields, literal ticker strings, and separately resolved historical securities. Group by a declared artifact version; never concatenate versions as new trading. Tabulate chamber/year/owner/direction/account context, transaction-date spread, repeated symbols within and across filings, and source/provider count discrepancies. Keep member-month summaries separate from filing sizes. For ambiguous identities provide bounded/unknown membership, not fabricated exact counts.
5. **Evaluate sensitivity before interpretation.** Show full empirical size distribution and thresholds 10/14/15/16/20; report both filing share and affected occurrence/member/security shares, missingness, exact boundary cases, and alternative row vs distinct-security definitions. Validate any claimed overlap only with eligible historical identity evidence. Inspect selected official context blinded to subsequent outcomes, record supported explanations, contradictory evidence and unresolved cases; use a second independent review for disagreement. Do not train or judge a passive label against the same size rule that created it.
6. **Enforce time and use-specific limits.** Intrinsic bulk features require evidence eligible at the Event's intrinsic boundary. Prior-filing/context features use the separately approved pre-session boundary; neither later amendments nor later annual holdings can explain earlier intent in primary Analysis. Current downloads alone prove retrieval-bound availability, not original publication time. Apply [approved event/time semantics](https://github.com/AviSharma01/signal-workspace/issues/6#issuecomment-5696776260); absent supported historical availability, label findings descriptive or later-information only. Outcome returns never choose thresholds or explanations.
7. **Stop with uncertainty.** Pilot success means reproducible counts, documented access/coverage, verified sampled occurrences, and an explicit accounting of what behavior remains unknowable. It does not mean a passive classifier exists. Any population claim needs a defensible sampling frame and broader validation; no independence of Events within a filing/member is implied.

## Handoff

[Choose bulk filing treatment for research cohorts](https://github.com/AviSharma01/signal-workspace/issues/8) can now consider a size descriptor with unknown intent, sensitivity/stratification, or evidence-specific context, without assuming passive behavior. Whether to flag, exclude, weight, or otherwise use bulk remains for that live decision. No additional foundational ticket is required merely to restate its question. The available evidence does not certify full filing-size distributions, an intent ground truth, complete historical eligibility, or a defensible universal cutoff.
