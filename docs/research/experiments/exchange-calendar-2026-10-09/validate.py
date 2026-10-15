#!/usr/bin/env python3
"""Read-only offline calendar comparison; emits JSON to stdout, never files."""

import argparse
from collections import Counter
from datetime import date, datetime, time, timedelta, timezone
from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
import sys

import exchange_calendars


HERE = Path(__file__).resolve().parent
PACKAGES = (
    "exchange_calendars", "korean_lunar_calendar", "numpy", "pandas", "pyluach",
    "python-dateutil", "six", "toolz", "tzdata",
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sunday(year, month, ordinal):
    first = date(year, month, 1)
    return first + timedelta(days=(6 - first.weekday()) % 7 + 7 * (ordinal - 1))


def utc_hours(day, early):
    # Independent NIST rules, not the library or its timezone conversion.
    dst = sunday(day.year, 3, 2) < day < sunday(day.year, 11, 1)
    offset = 4 if dst else 5
    return [
        datetime.combine(day, time(9 + offset, 30), timezone.utc),
        datetime.combine(day, time((13 if early else 16) + offset), timezone.utc),
    ]


def stamp(value):
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def rows_for(name, start, end):
    schedule = exchange_calendars.get_calendar(name, start=start, end=end).schedule
    return [[label.date().isoformat(), stamp(row["open"]), stamp(row["close"])]
            for label, row in schedule.iterrows()]


def validate(expectations_path):
    require(version("exchange_calendars") == "4.13.2", "requires exchange_calendars==4.13.2")
    raw = expectations_path.read_bytes()
    e = json.loads(raw)
    start, end = map(date.fromisoformat, (e["evaluation_start"], e["evaluation_cutoff"]))
    require((start.isoformat(), end.isoformat()) == ("2021-01-01", "2026-10-08"), "scope changed")
    closed_list = [d for dates in e["closed_weekdays"].values() for d in dates]
    early_list = [d for dates in e["early_closes"].values() for d in dates]
    require(len(closed_list) == len(set(closed_list)) == 57, "expected 57 unique closures")
    require(len(early_list) == len(set(early_list)) == 10, "expected 10 unique early closes")
    closed, early = set(closed_list), set(early_list)
    for value in closed | early:
        day = date.fromisoformat(value)
        require(start <= day <= end and day.weekday() < 5, f"invalid expected weekday: {value}")
    require(not closed & early, "closed and early-close expectations overlap")
    expected = []
    day = start
    while day <= end:
        label = day.isoformat()
        if day.weekday() < 5 and label not in closed:
            expected.append([label, *map(stamp, utc_hours(day, label in early))])
        day += timedelta(days=1)
    observed = rows_for("XNYS", start.isoformat(), end.isoformat())
    require(observed == expected, "date/open/close sequence differs from independent expectations")
    counts = dict(sorted(Counter(row[0][:4] for row in observed).items()))
    require(counts == e["session_counts"], "annual session counts differ")
    require(len(observed) == 1448, "expected 1448 sessions")
    by_date = {row[0]: row[1:] for row in observed}
    require(early <= by_date.keys(), "early-close date is not a session")
    for before, after in e["dst_session_pairs"]:
        require(by_date[before] != by_date[after], "invalid DST pair")
        require(by_date[before][0][11:16] != by_date[after][0][11:16], "DST open did not change")
        for label in (before, after):
            require(by_date[label] == list(map(stamp, utc_hours(date.fromisoformat(label), False))),
                    f"DST timestamp mismatch: {label}")
    dates = list(by_date)
    for before, after in e["year_boundary_pairs"]:
        require(dates[dates.index(before) + 1] == after, f"year boundary mismatch: {before}")
        for label in (before, after):
            require(by_date[label] == list(map(stamp, utc_hours(date.fromisoformat(label), False))),
                    f"year-boundary timestamp mismatch: {label}")
    for label in e["open_controls"]:
        require(label in by_date, f"open control missing: {label}")
    for name in e["aliases"]:
        require(rows_for(name, start.isoformat(), end.isoformat()) == observed, f"alias differs: {name}")
    # Exact bytes: UTF-8, no header, comma-separated date/open/close, LF per row,
    # final LF; timestamps have second precision, UTC Z. No pandas CSV defaults.
    canonical = "".join(",".join(row) + "\n" for row in observed).encode("utf-8")
    return {
        "status": "PASS", "recorded_reproduction_date": "2026-10-15",
        "evaluation_start": start.isoformat(), "evaluation_cutoff": end.isoformat(),
        "sessions": len(observed), "closed_weekdays": len(closed),
        "session_counts": counts, "early_closes": e["early_closes"],
        "dst_timestamp_controls": 4 * len(e["dst_session_pairs"]),
        "year_boundary_pairs": len(e["year_boundary_pairs"]), "aliases": e["aliases"],
        "date_or_timestamp_mismatches": 0,
        "schedule_serialization": "UTF-8 CSV, no header, date/open_UTC/close_UTC, YYYY-MM-DD / YYYY-MM-DDTHH:MM:SSZ, LF rows including final LF",
        "schedule_sha256": sha256(canonical).hexdigest(),
        "expectations_sha256": sha256(raw).hexdigest(),
        "validator_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "python_version": sys.version.split()[0],
        "packages": {name: version(name) for name in PACKAGES},
        "historical_digest_status": "Original serialization and artifact unavailable; original digest is not verified by this reproduction",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expectations", type=Path, default=HERE / "expectations.json")
    parser.add_argument("--check", action="store_true", help="compare output with retained result.json")
    args = parser.parse_args()
    result = validate(args.expectations)
    if args.check:
        require(result == json.loads((HERE / "result.json").read_text()), "retained result differs")
    print(json.dumps(result, indent=2) + "\n", end="")


if __name__ == "__main__":
    main()
