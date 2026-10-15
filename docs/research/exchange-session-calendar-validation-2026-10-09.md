# Bounded U.S. exchange/session-calendar validation

Observation date: **2026-10-09**. Research/validation only: no provider
selection or integration, production-code change, Git operation, or #31
readiness change.

Reproduction added **2026-10-15** with a small retained [offline validation
packet](experiments/exchange-calendar-2026-10-09/README.md). It independently
reconstructs the same historical scope and confirms the counts and timestamp
comparisons below. The October 9 schedule digest itself remains unverified:
its original serialization and schedule were not retained. The new packet
defines its own exact serialization and digest; it does not backdate evidence.

**Decision: PLAUSIBLE.** Pinned `exchange_calendars==4.13.2` is a defensible
free implementation candidate for the approved U.S. regular-equity session
component. Across every completed session from 2021-01-01 through the
conservative cutoff **2026-10-08**, its XNYS schedule matched independently
constructed official expectations for session dates, regular opens/closes,
early closes, DST conversion, the 2025 Carter closure, and year boundaries.
This validates a calendar subcomponent only. It does not establish that any
provider's daily OHLCV represents those regular sessions.

## Boundary and method

First inspected: [#31](https://github.com/AviSharma01/signal-workspace/issues/31),
the [provider-neutral contract](../market-data-conformance.md),
[#26](https://github.com/AviSharma01/signal-workspace/issues/26), the
[approved V2 semantics](../specs/signal-v2.md). Historical research inputs also
included the free-composite synthesis, historical-identity screen and OpenFIGI
experiment; they are not required to reproduce this calendar comparison.
The applicable contract requires independently attributed expectations; the
candidate calendar cannot be its own ground truth.

An isolated `/tmp` environment used Python 3.13.15,
`exchange-calendars 4.13.2`, pandas 3.0.6, NumPy 2.5.3, tzdata 2026.5 and
python-dateutil 2.9.0.post0. No package or dependency was added to the project.
Expected sessions were constructed as weekdays minus the full-closure dates in
Nasdaq's official [2021](https://www.nasdaqtrader.com/content/technicalsupport/2021tradingcalendar.pdf),
[2022](https://www.nasdaqtrader.com/content/technicalsupport/2022tradingcalendar.pdf),
[2023](https://www.nasdaqtrader.com/content/technicalsupport/2023tradingcalendar.pdf),
[2024](https://www.nasdaqtrader.com/content/technicalsupport/2024tradingcalendar.pdf),
[2025](https://www.nasdaqtrader.com/content/technicalsupport/2025tradingcalendar.pdf)
and [2026 calendar index](https://nasdaqtrader.com/Trader.aspx?id=Calendar),
cross-checked against NYSE's [hours/holiday calendar](https://www.nyse.com/markets/hours-calendars).
Expected timestamps used the exchanges' 09:30–16:00 ET core session and
13:00 ET early close, independently converted using NIST's
[EST UTC-5 / EDT UTC-4 definitions](https://www.nist.gov/pml/time-and-frequency-division/local-time-faqs).

The check compared the complete date sequence, not only samples. It then
checked every observed local open and close, the exact expected early-close
set, 44 exact ET/UTC timestamp controls, closed/open boundary controls, and
NYSE/Nasdaq/Arca/American aliases. Expected and observed values were represented
separately before comparison.

## Results

| Year | Completed scope | Expected / observed sessions | Expected / observed early closes | Result |
|---|---:|---:|---|---|
| 2021 | full year | 252 / 252 | 2021-11-26 / same | PASS |
| 2022 | full year | 251 / 251 | 2022-11-25 / same | PASS |
| 2023 | full year | 250 / 250 | 2023-07-03, 2023-11-24 / same | PASS |
| 2024 | full year | 252 / 252 | 2024-07-03, 2024-11-29, 2024-12-24 / same | PASS |
| 2025 | full year | 250 / 250 | 2025-07-03, 2025-11-28, 2025-12-24 / same | PASS |
| 2026 | through 2026-10-08 | 193 / 193 | none / none | PASS |

The complete comparison covered **1,448 sessions** and **57 expected closed
weekdays**, including the extraordinary closure. There were **zero date,
open-time, close-time or early-close mismatches**. All session labels equaled
the America/New_York local date of both timestamps. Every completed session
opened at 09:30 ET and closed at either 16:00 ET or the independently expected
13:00 ET.

| Required case | Independent expectation | `4.13.2` observation |
|---|---|---|
| Ordinary full sessions | 09:30–16:00 ET; winter 14:30–21:00Z, summer 13:30–20:00Z | Exact match across all sessions; representative pre/post-DST controls below matched |
| July 3 | 2023, 2024 and 2025: 09:30–13:00 EDT = 13:30–17:00Z; 2021/2022 weekend; 2026-07-03 full Independence Day-observed closure | Exact timestamps on all three early closes; 2026-07-03 absent |
| Black Friday | 2021-11-26, 2022-11-25, 2023-11-24, 2024-11-29 and 2025-11-28: 09:30–13:00 EST = 14:30–18:00Z | Exact match on all five |
| Christmas Eve | 2021-12-24 full Christmas-observed closure; 2022/2023 weekend; 2024-12-24 and 2025-12-24: 09:30–13:00 EST = 14:30–18:00Z | Exact match; no invented weekday session in 2021 |
| Juneteenth boundary | 2021-06-18 open; closures begin in 2022 | Exact match. Nasdaq explicitly said its U.S. markets remained open in 2021 ([notice](https://www.nasdaqtrader.com/TraderNews.aspx?id=ETA2021-45)) |
| Carter mourning closure | 2025-01-09 is not a trade date; normal sessions 2025-01-08 and 2025-01-10 are 09:30–16:00 EST = 14:30–21:00Z | Jan. 9 absent; Jan. 8/10 exact. Independent [Nasdaq notice](https://classic.nasdaqtrader.com/TraderNews.aspx?id=ECA2024-632) establishes the equity closure and [NYSE memo](https://www.nyse.com/publicdocs/nyse/markets/american-options/rule-interpretations/2025/National_Day_of_Mourning_20250102.pdf) corroborates the market closure; the [SEC notice](https://www.sec.gov/newsroom/whats-new/edgar-closed-january-9-2025) supplies federal/EDGAR context, not exchange-session proof |

For DST, the last Friday before and first Monday after every completed spring
transition (2021–2026) changed from **14:30–21:00Z** to **13:30–20:00Z** while
remaining 09:30–16:00 ET. The corresponding completed fall pairs (2021–2025)
changed back from **13:30–20:00Z** to **14:30–21:00Z**. The tested pairs were
March 12/15 and November 5/8 (2021), March 11/14 and November 4/7 (2022),
March 10/13 and November 3/6 (2023), March 8/11 and November 1/4 (2024),
March 7/10 and October 31/November 3 (2025), and March 6/9 (2026). The 2026
fall transition was not yet a completed-session case.

Year-boundary sequences also matched exactly, with all listed endpoints normal
09:30–16:00 EST sessions: 2021-12-31 → 2022-01-03,
2022-12-30 → 2023-01-03, 2023-12-29 → 2024-01-02,
2024-12-31 → 2025-01-02, and 2025-12-31 → 2026-01-02.

## Versioning, retention and alignment

The candidate is Apache-2.0 and has versioned PyPI wheel and source artifacts.
For 4.13.2, PyPI records the 2026-03-10 release and SHA-256
`fc5a2ad0d61b5c3a6539a3061cd4cbb55c59f4a903455cec7926e4b798919996`
for the wheel and
`a9459425dd64142cd54fbc639847403c7e0c33d60fbc326c94fc1d6bd127f002`
for the source distribution ([release files](https://pypi.org/project/exchange_calendars/4.13.2/)).
The October 9 observation reported two network-free processes, 1,448 rows and
schedule SHA-256
`98b8529aa6fc8a01bbd7228064a5d6923b51bb80f80fba232f9480f138b1b1ba`.
Its original generated schedule and serialization are unavailable, so that
digest is a historical reported observation, **not independently reproduced
evidence**.

On October 15, a fresh isolated Python 3.13.15 environment matched the original
package versions. Independently reconstructed exchange expectations produced
1,448 matching sessions, all 57 weekday closures, all ten early closes, 44 DST
timestamp controls, five year boundaries and identical XNAS/ARCX/XASE aliases.
Two fresh network-free processes produced the same retained
[result](experiments/exchange-calendar-2026-10-09/result.json), including a
new schedule SHA-256
`120294a88f1080277967d8d8a891553d912f7f944716918d19e98837cbe70cf1`.
Its exact UTF-8 CSV serialization is defined in the packet. The
[expectations](experiments/exchange-calendar-2026-10-09/expectations.json),
[validator](experiments/exchange-calendar-2026-10-09/validate.py), their hashes,
environment manifest and result are retained; the schedule is regenerated,
not stored. Moving the Carter closure or one early close in temporary copies
of the expectations failed the complete comparison as intended. Source review
occurred October 15 and does not prove exact earlier publication contents or
first-public timing of the live 2026 exchange pages.

The library's XNYS source declares America/New_York, 09:30/16:00 regular hours,
13:00 early closes and the Carter closure ([4.13.2 source](https://github.com/gerrymanoim/exchange_calendars/blob/4.13.2/exchange_calendars/exchange_calendar_xnys.py)).
Its dispatcher aliases XNAS, ARCX, XASE and BATS to XNYS
([4.13.2 source](https://github.com/gerrymanoim/exchange_calendars/blob/4.13.2/exchange_calendars/calendar_utils.py)).
The validation confirmed byte-equivalent scoped schedules for XNAS, ARCX and
XASE. Independent NYSE and Nasdaq calendars agreed throughout the tested
period; Cboe also specifies 09:30–16:00 ET regular hours and the same holiday /
early-close pattern ([hours and holidays](https://www.cboe.com/about/hours/)),
and its equities exchanges also closed for Carter
([notice](https://cdn.cboe.com/resources/schedule_update/2025/Update-Cboe-to-Observe-National-Day-of-Mourning-on-Thursday-January-9-2025.pdf)).
No listing-calendar difference was found that prevents one regular-session
calendar for the approved primary U.S.-listed-equity cohort.

For security/SPY alignment, use the local session date as the exact join key and
require identical UTC open/close timestamps from the retained calendar version.
SPY's ARCX alias and the tested primary U.S. equity aliases share those keys and
timestamps. Never substitute a nearest date or shorten a window. Listing
transfers, unsupported venues, instrument-specific halts, IPO/delisting days,
and missing bars remain identity/provider observations and can still make a
measurement unavailable; calendar equality does not manufacture a bar.

## Remaining unknowns and stop decision

There were no mismatches in the completed 2021–2026 scope. The bounded
limitations are:

- Extraordinary closures are release-sensitive. A March 2025 issue documents
  that the then-current library still treated 2025-01-09 as a session
  ([issue](https://github.com/gerrymanoim/exchange_calendars/issues/464)); 4.13.2
  now passes. Pinning gives reproducibility, not automatic correctness after a
  newly announced closure. Each evaluation needs a retained authoritative
  closure check or an approved update procedure.
- November/December 2026 were scheduled but not completed at the cutoff, so
  their advertised Black Friday and Christmas Eve early closes are not counted
  as completed-session validation.
- This did not exhaustively audit every small U.S. venue's historical notices.
  The primary NYSE/Nasdaq calendars, relevant aliases and Cboe corroboration
  revealed no conflicting regular-session date/time rule. Any future listing
  on an unsupported venue must fail closed until its calendar compatibility is
  evidenced.
- The library itself is implementation evidence, not an exchange authority.
  Retain the independent expectations with the pinned result.

**Broad calendar-source research can stop.** The component is sufficiently
defensible to move from an untested plausible candidate to a validated
**PLAUSIBLE** subcomponent, subject to version pinning, retained independent
expectations and reproducible schedule digests, and authoritative
extraordinary-closure checks. It remains
below production readiness and does not change #31.

The unresolved gates belong elsewhere: whether a price source's OHLCV is truly
unadjusted regular-session data; complete historically scoped security/listing
identity; corporate-action/terminal-event coverage; provider retention,
revision and workload evidence. A correct calendar cannot prove or repair any
of them.
