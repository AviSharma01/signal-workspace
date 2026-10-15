# Calendar reproduction packet

Historical evaluation: **2021-01-01 through 2026-10-08**, inclusive.
Reproduction and independent-source review: **2026-10-15**. The directory date
identifies the original research note; it is not the reproduction date.

`expectations.json` contains independently transcribed exchange holiday and
early-close facts, source URLs, and boundary controls. The validator constructs
expected weekdays and UTC hours without reading the candidate's holiday rules
or timezone output. NIST's DST rule and EST/EDT offsets determine expected UTC
hours; `exchange_calendars` supplies only the observed schedule. All 1,448 dates
and both timestamps are compared, as are the exact early-close set, Carter
closure, 44 DST timestamp controls, five year boundaries and three aliases.

The annual Nasdaq PDFs' colored full/early-closure markers were visually
reviewed. The separate December 2024 Nasdaq notice supplies the Carter closure
missing from the annual 2025 PDF. These expectations were reconstructed on the
reproduction date, not retained from the October 9 run. The live 2026 calendar
pages were reviewed on October 15; this does not establish their exact earlier
publication contents or first-public timestamps. No daily price/provider
dataset or copied exchange document is included.

Use a separate Python 3.13.15 environment, outside the repository. The recorded
versions are:

```text
exchange_calendars==4.13.2
korean_lunar_calendar==0.4.0
numpy==2.5.3
pandas==3.0.6
pyluach==2.3.0
python-dateutil==2.9.0.post0
six==1.17.0
toolz==1.2.0
tzdata==2026.5
```

After installing those versions, run from the repository root:

```sh
/path/to/isolated/python docs/research/experiments/exchange-calendar-2026-10-09/validate.py --check
```

The validator uses no network and writes no files. It exits nonzero on a
mismatch. `--check` compares the computed summary, environment versions and
input/script hashes with `result.json`; omit it to inspect another environment
without claiming exact result reproduction. `recorded_reproduction_date` names
this retained experiment, not the date of a future invocation.

The schedule digest is over explicit UTF-8 CSV bytes with no header: ascending
`date,open_UTC,close_UTC` rows, second-precision `YYYY-MM-DDTHH:MM:SSZ`
timestamps, LF after every row including the last. The generated schedule is
small enough to regenerate and is not retained. Two fresh processes reproduced
the result. Temporary mutated expectations (moving the Carter closure to
January 8 and moving one early close) were rejected by the complete comparison.

The original October 9 digest has no retained serialization or schedule. This
packet establishes a new documented digest, **not verification of that original
digest**. A passing bounded check certifies neither provider session semantics,
future extraordinary closures, historical source-publication timing, nor #31
production readiness.
