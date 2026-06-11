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
from datetime import date as date_cls
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=date_cls.today().isoformat(),
                    help="YYYY-MM-DD (default: today)")
    ap.add_argument("--csv", default=str(Path.cwd() / "diet_log.csv"),
                    help="path to diet_log.csv (default: ./diet_log.csv)")
    args = ap.parse_args()

    totals = {"calories": 0.0, "protein_g": 0.0, "carb_g": 0.0, "fat_g": 0.0}
    rows = []
    training_day = None
    with open(args.csv, newline="") as f:
        for row in csv.DictReader(f):
            if row["date"] != args.date:
                continue
            rows.append(row)
            for k in totals:
                try:
                    totals[k] += float(row[k] or 0)
                except (ValueError, KeyError):
                    pass
            if training_day is None:
                training_day = row.get("training_day", "").upper() == "TRUE"

    label = "training day" if training_day else "rest day" if training_day is False else "unmarked"
    print(f"{args.date} ({label})")
    print(f"entries: {len(rows)}")
    print(f"kcal: {totals['calories']:.0f} | P {totals['protein_g']:.0f} g | "
          f"C {totals['carb_g']:.0f} g | F {totals['fat_g']:.0f} g")


if __name__ == "__main__":
    main()
