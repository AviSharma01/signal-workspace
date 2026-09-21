# Raw Consensus window feasibility: bounded disclosure-only check

Observed **2026-09-16 21:25 UTC / 2026-09-17 Asia/Kolkata** at checkout
`9e89e7dc0933f576d23eb142fd33db682cc8e04f`. Research evidence for
[Choose primary and sensitivity Raw Consensus windows](https://github.com/AviSharma01/signal-workspace/issues/15),
not a window selection, approved methodology change, or source-readiness certification.

## Result

**The approved Raw Consensus is not computable from the inspected local disclosure
table.** Its stored fields do not establish supported original publication
availability, historically resolved security/member identity, retrieved official
artifact/version provenance, or correction-aware contextual state. Consequently,
this check cannot report distributions of Raw Consensus, Other Reporting Members,
zero-peer Events, or unresolved window-membership rates for any candidate length.
These results are **unavailable**, not observed zeros.

This is a finding about the inspected representation, not an exhaustive audit of
external artifacts, and not proof that historical publication evidence cannot be
obtained. No linked official document was retrieved in this check. There is no
certified eligible target population against which to calculate an exclusion
percentage; calling every stored row an excluded eligible Event would itself
invent eligibility.

The illustrative 7/14/30/60/90 calendar-day grid was **not calculated or selected**.
Using `disclosed` as publication time and ticker strings as security identities
would produce a different, unsupported proxy. A grid cannot repair these missing
defining inputs. No candidate length was rejected for sparsity or coverage.

## Authorized purpose and exposure record

The developer specified recent clustering of publicly disclosed participation
around the target Event as the descriptive meaning of the primary window, with a
longer pre-specified sensitivity window. Neither implies predictive or economic
superiority. The bounded check may expose clearly unusable choices and the scale
of the measure; it must not choose a window by maximizing nonzero counts, member
separation, or an attractive distribution.

The developer reports, **to the best of their recollection**, no inspection of
market outcomes or predictive performance conditional on particular Raw Consensus
lookbacks. Earlier discussion of +7/+30/+90 concerned forward outcome horizons,
not publication lookbacks. This is a qualified recollection, not proof of complete
project-wide outcome blindness. This check queried no prices, returns, benchmarks,
significance, predictive/anomaly performance, or downstream market results. Prior
disclosure research notes were read; enriched Kadoa JSON rows were not read.

## Scope, provenance, and observed inventory

Read-only SQLite access to `server/signal.db`: first enumerated table names, then
inspected only the `disclosures` schema and selected disclosure columns. Other
tables' data and schemas were not queried. No ingestion, source refresh, external
artifact acquisition, application change, or data write occurred.

The inspected table has `id`, `member`, `chamber`, `ticker`, `trade_type`,
`amount_raw`, `amount_low`, `amount_high`, `tx_date`, `disclosed`, `asset`, `link`,
and `fetched_at`. The schema labels `disclosed` only as `YYYY-MM-DD`, and `link` as
a PTR URL. It has a unique constraint on
`(member, ticker, trade_type, tx_date, amount_raw, link)`. There are no dedicated
raw-artifact/version, publication-evidence, mapping-history, or amendment-lineage
fields in this table. Its value-based uniqueness constraint cannot by itself
preserve separate identical reported occurrences.

The following are **stored-row diagnostics**, not verified Events, a primary
Analysis cohort, population coverage, or an independence claim:

| Diagnostic | Observed value |
|---|---:|
| Stored rows | 5,224 |
| Chamber labels | House 4,623; Senate 601 |
| Direction labels | buy 2,668; sell 2,556 |
| Distinct exact member strings | 95 |
| Distinct exact ticker strings | 1,094 |
| Distinct nonempty link strings | 396 |
| Missing values in queried member/chamber/ticker/direction/date/link/fetch fields | 0 |
| Strict ISO calendar-date strings in `disclosed` | 5,224; 2025-06-02–2026-06-02 |
| Strict ISO calendar-date strings in `tx_date` | 5,224; 2015-05-08–2026-12-26 |
| `disclosed` year 2025 | House 3,278; Senate 328 |
| `disclosed` year 2026 | House 1,345; Senate 273 |
| Link hostname strings | House Clerk 4,623; Senate eFD 601 |
| `fetched_at`, all rows | 1788431578479 Unix milliseconds |

An official-looking link is not evidence that its artifact was retrieved or that
its version was public at a historical cutoff. A populated ISO date is not
supported publication availability. The transaction-date maximum extends past the
observation date; no cause was diagnosed and no values were repaired. The single
fetch value cannot establish historical first publication. Source snapshot
identity and capture lineage were not reconstructed. In particular, the row count
matching [reported historical characteristics](../data/disclosure-characteristics.md)
does not reproduce the old 5,384-row source or prove the reported collapse history.

## Why the missing evidence matters

The approved decisions [Define Event, Watch Event eligibility, and point-in-time semantics](https://github.com/AviSharma01/signal-workspace/issues/6)
and [Define Raw Consensus counting and grouping semantics](https://github.com/AviSharma01/signal-workspace/issues/12)
require original supported publication availability within
`[start, target derived session open)`, a strictly-before-open contextual cutoff,
and correction-aware interpretations supported at that cutoff. Date-only
publication applies the after-day-end rule; filing date alone does not qualify.
An unresolved publication interval crossing the start prevents definitive
membership. Current literal tickers do not establish historical instruments.

The existing [source research](disclosure-source-evidence-2026-09-15.md),
[Kadoa/House evidence](kadoa-house-bulk-evidence-2026-09-15.md), and
[bulk classification evidence](bulk-filing-classification-evidence-2026-09-16.md)
do not supply a verified historical publication panel. The annual House archive
sample is an index with filing dates; the two provider samples are convenience
samples without established historical publication/version lineage. Those notes'
checks were not re-performed here and their external facts are not newly verified.

## Minimum bounded follow-up if empirical count diagnostics remain required

Before acquiring more rows, identify **one frozen candidate evidence inventory**
that can actually support original publication boundaries, official versions,
occurrence/member/historical-security identity, and corrections available before
each target cutoff. Record the inventory's chamber/time scope and selection rule
without reference to outcomes. Begin with an evidence gate on a small fixed set
of candidate targets, rather than interpreting provider dates by assumption.

For each admitted target, candidate peer evidence must cover the entire longest
illustrative lookback and the pre-session interval, not merely an arbitrary
handful of linked filings. Declare the search coverage and retrieval stop rule;
an incomplete search cannot silently become a complete Congressional count.
Freeze the candidate lengths and boundary convention before running counts.
Preserve original publication intervals and unresolved start-boundary cases;
report target failures separately from peer exclusions, with explicit denominators
and reason-specific counts. Any resulting sample statistics would describe that
fixed supported sample, not population frequencies without further evidence.

If the initial evidence gate fails, stop and report unavailability again. Merely
fetching official PDFs today will establish retrieval-bound availability, not
historical first publication. A separately agreed evidence pilot or an explicit
decision to defer empirical selection is needed; this note neither authorizes
broad ingestion nor substitutes a proxy for the approved measure.

## Reproduction

The query projection below was hashed in a single read transaction. Its canonical
JSON bytes numbered **1,317,287** and SHA-256 was
`df06b19290d909160afc6f5e28a52aabc2a12cce627048b95e367506761c4418`.
This identifies the inspected columns, not the entire database or source corpus.
The local database is mutable and untracked; a future hash mismatch means the
inventory is no longer the same snapshot. The script prints aggregate fields
only and accesses no other table.

```python
import collections, datetime, hashlib, json, sqlite3, urllib.parse
from pathlib import Path

p = Path('server/signal.db').resolve()
c = sqlite3.connect(p.as_uri() + '?mode=ro', uri=True)
c.execute('PRAGMA query_only=ON')
c.execute('BEGIN')
cols = ['id', 'member', 'chamber', 'ticker', 'trade_type',
        'tx_date', 'disclosed', 'link', 'fetched_at']
rows = [dict(zip(cols, r)) for r in c.execute(
    'SELECT ' + ','.join(cols) + ' FROM disclosures ORDER BY id')]
b = json.dumps(rows, ensure_ascii=False, sort_keys=True,
               separators=(',', ':')).encode()
print('projection', len(rows), len(b), hashlib.sha256(b).hexdigest())
for field in ('chamber', 'trade_type'):
    print(field, dict(collections.Counter(r[field] for r in rows)))
for field in ('member', 'ticker', 'link'):
    print('distinct', field, len({r[field] for r in rows if r[field]}))
print('missing', {k: sum(r[k] is None or isinstance(r[k], str)
                       and not r[k].strip() for r in rows) for k in cols[1:]})
for field in ('disclosed', 'tx_date'):
    valid, invalid = [], 0
    for r in rows:
        try:
            d = datetime.date.fromisoformat(r[field])
            if d.isoformat() != r[field]:
                raise ValueError()
            valid.append(d)
        except (ValueError, TypeError):
            invalid += 1
    print(field, len(valid), invalid,
          str(min(valid)) if valid else None, str(max(valid)) if valid else None)
print('year/chamber', sorted(collections.Counter(
    (r['disclosed'][:4] if isinstance(r['disclosed'], str) else '(missing)',
     r['chamber']) for r in rows).items()))
print('link hosts', dict(collections.Counter(
    urllib.parse.urlparse(r['link'] or '').hostname for r in rows)))
print('fetch range', min((r['fetched_at'] for r in rows), default=None),
      max((r['fetched_at'] for r in rows), default=None))
c.rollback()
c.close()
```
