#!/usr/bin/env python3
"""Recommend a PAL value from recent training frequency in diet_log.csv.

Counts unique dates marked `training_day=TRUE` in the past N days
(default 14), normalises to sessions/week, and buckets to the standard
Mifflin-St Jeor PAL table:

    < 1.0 /wk -> 1.20   (sedentary)
    < 3.0 /wk -> 1.375  (light)
    < 6.0 /wk -> 1.55   (moderate)
    < 8.0 /wk -> 1.725  (heavy)
    else      -> 1.90   (very heavy)

If the log has < 3 unique dates with ANY entry in the window, prints a
"log sparse" warning but still outputs the recommendation -- the caller
should decide whether to apply it or keep the current PAL.

Example:
    pal-from-log.py --csv ~/diet-coach/diet_log.csv
    pal-from-log.py --csv ./diet_log.csv --days 28
"""
import argparse
import csv
import sys
from datetime import date as date_cls, timedelta
from pathlib import Path

REQUIRED_COLS = {"date", "training_day"}


def bucket_pal(per_week):
    if per_week < 1.0:
        return 1.20, "sedentary"
    if per_week < 3.0:
        return 1.375, "light"
    if per_week < 6.0:
        return 1.55, "moderate"
    if per_week < 8.0:
        return 1.725, "heavy"
    return 1.90, "very heavy"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=str(Path.cwd() / "diet_log.csv"),
                    help="path to diet_log.csv (default: ./diet_log.csv)")
    ap.add_argument("--days", type=int, default=14,
                    help="rolling window size in days (default: 14)")
    ap.add_argument("--today", default=date_cls.today().isoformat(),
                    help="reference 'today' as YYYY-MM-DD (default: actual today)")
    args = ap.parse_args()

    if args.days < 1:
        print(f"error: --days {args.days} must be >= 1", file=sys.stderr)
        sys.exit(1)

    try:
        today = date_cls.fromisoformat(args.today)
    except ValueError:
        print(f"error: --today {args.today!r} is not valid YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)
    window_start = today - timedelta(days=args.days - 1)

    try:
        f = open(args.csv, newline="")
    except FileNotFoundError:
        print(f"error: diet_log.csv not found at {args.csv}", file=sys.stderr)
        print("hint: pass --csv <path> or run from the directory containing diet_log.csv",
              file=sys.stderr)
        sys.exit(1)

    all_dates = set()
    training_dates = set()
    with f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLS - set(reader.fieldnames or [])
        if missing:
            print(f"error: {args.csv} missing columns: {sorted(missing)}", file=sys.stderr)
            sys.exit(1)
        for row in reader:
            try:
                d = date_cls.fromisoformat(row["date"])
            except (ValueError, KeyError):
                continue
            if not (window_start <= d <= today):
                continue
            all_dates.add(d)
            if row.get("training_day", "").strip().upper() == "TRUE":
                training_dates.add(d)

    print(f"window: {window_start.isoformat()} -- {today.isoformat()} ({args.days} days)")
    print(f"training days: {len(training_dates)} "
          f"({len(training_dates) * 7 / args.days:.1f} /week)")

    if not all_dates:
        print("warning: no log entries in window -- keep current PAL until more data is logged")
        return

    if len(all_dates) < 3:
        print(f"warning: only {len(all_dates)} unique log date(s) in window -- "
              f"data sparse, treat recommendation with caution")

    per_week = len(training_dates) * 7 / args.days
    pal, label = bucket_pal(per_week)
    print(f"recommended PAL: {pal} ({label})")


if __name__ == "__main__":
    main()
