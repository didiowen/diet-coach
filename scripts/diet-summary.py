#!/usr/bin/env python3
"""Daily totals from diet_log.csv.

Sums calories/protein/carb/fat for a given date (default today) and reports
the training-day flag if present.

Example:
    diet-summary.py
    diet-summary.py --date 2026-06-10
    diet-summary.py --csv /path/to/diet_log.csv
"""
import argparse
import csv
import sys
from datetime import date as date_cls
from pathlib import Path

REQUIRED_COLS = {"date", "calories", "protein_g", "carb_g", "fat_g"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date_cls.today().isoformat(),
                    help="YYYY-MM-DD (default: today)")
    ap.add_argument("--csv", default=str(Path.cwd() / "diet_log.csv"),
                    help="path to diet_log.csv (default: ./diet_log.csv)")
    args = ap.parse_args()

    try:
        date_cls.fromisoformat(args.date)
    except ValueError:
        print(f"error: --date {args.date!r} is not valid YYYY-MM-DD", file=sys.stderr)
        sys.exit(1)

    totals = {"calories": 0.0, "protein_g": 0.0, "carb_g": 0.0, "fat_g": 0.0}
    rows = []
    training_day = None
    try:
        f = open(args.csv, newline="")
    except FileNotFoundError:
        print(f"error: diet_log.csv not found at {args.csv}", file=sys.stderr)
        print("hint: pass --csv <path> or run from the directory containing diet_log.csv",
              file=sys.stderr)
        sys.exit(1)
    with f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLS - set(reader.fieldnames or [])
        if missing:
            print(f"error: {args.csv} missing columns: {sorted(missing)}", file=sys.stderr)
            sys.exit(1)
        for row in reader:
            if row["date"] != args.date:
                continue
            rows.append(row)
            for k in totals:
                try:
                    totals[k] += float(row[k] or 0)
                except (ValueError, KeyError):
                    pass
            if training_day is None:
                training_day = row.get("training_day", "").strip().upper() or None

    if not rows:
        print(f"{args.date}: 當日無記錄 (no entries in {args.csv})")
        return

    label = {"TRUE": "training day", "MID": "mid-intensity day", "FALSE": "rest day"}.get(training_day, "unmarked")
    print(f"{args.date} ({label})")
    print(f"entries: {len(rows)}")
    print(f"kcal: {totals['calories']:.0f} | P {totals['protein_g']:.0f} g | "
          f"C {totals['carb_g']:.0f} g | F {totals['fat_g']:.0f} g")


if __name__ == "__main__":
    main()
