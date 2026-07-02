#!/usr/bin/env python3
"""
food-ref-append.py — atomic append to the shared food_reference.csv

Uses fcntl.flock for cross-process serialization. Dedupes by (food_name, source).
Skip if already present, append otherwise.

Race-safe for concurrent invocation from multiple Claude sessions (multi-tenant
ctb bot). Whichever process acquires the exclusive lock first wins; others
wait, then re-check for the dedupe key the winner may have just added.

Usage:
  python3 food-ref-append.py \\
    --food-name "統一陽光無加糖高纖豆漿" \\
    --source "統一" \\
    --serving-size-g 400 \\
    --calories 167.4 \\
    --protein-g 15.0 \\
    --carb-g 14.0 \\
    --fat-g 7.6 \\
    --notes "每盒400ml；無加糖；菊苣纖維8.5g；標示值"

Exit codes:
  0 — appended OR duplicate skipped (both are "idempotent success")
  1 — error (file missing, invalid args, etc.)
"""

import argparse
import csv
import fcntl
import os
import sys
from pathlib import Path

# Override via env var DIET_COACH_FOOD_REF; default is the public-template layout.
CSV_PATH = Path(os.environ.get(
    "DIET_COACH_FOOD_REF",
    str(Path.home() / "diet-coach" / "food_reference.csv"),
))
REQUIRED_FIELDS = [
    "food_name", "source", "serving_size_g", "calories",
    "protein_g", "carb_g", "fat_g", "notes",
]
# Micronutrients: optional, only filled when a label/DB provides them (else "").
OPTIONAL_FIELDS = ["calcium_mg", "iron_mg"]
FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS
NUMERIC_FIELDS = ["serving_size_g", "calories", "protein_g", "carb_g", "fat_g"]
OPTIONAL_NUMERIC_FIELDS = ["calcium_mg", "iron_mg"]


def validate_numeric(row):
    errs = []
    for f in NUMERIC_FIELDS:
        raw = row[f]
        try:
            v = float(raw)
        except ValueError:
            errs.append(f"--{f.replace('_', '-')} {raw!r} is not a number")
            continue
        if v != v:  # NaN check
            errs.append(f"--{f.replace('_', '-')} is NaN")
        elif v < 0:
            errs.append(f"--{f.replace('_', '-')} {v} must be >= 0")
    # Optional micronutrients: empty is allowed; validate only when provided.
    for f in OPTIONAL_NUMERIC_FIELDS:
        raw = row.get(f, "")
        if raw == "" or raw is None:
            continue
        try:
            v = float(raw)
        except ValueError:
            errs.append(f"--{f.replace('_', '-')} {raw!r} is not a number")
            continue
        if v != v:
            errs.append(f"--{f.replace('_', '-')} is NaN")
        elif v < 0:
            errs.append(f"--{f.replace('_', '-')} {v} must be >= 0")
    return errs


def main() -> int:
    p = argparse.ArgumentParser(
        description="Atomically append a row to food_reference.csv (flock + dedupe).",
    )
    for f in REQUIRED_FIELDS:
        # notes is a schema column but has no meaningful "required" value
        p.add_argument(f"--{f.replace('_', '-')}", required=(f != "notes"),
                       default="", help=f"value for {f} column")
    for f in OPTIONAL_FIELDS:
        p.add_argument(f"--{f.replace('_', '-')}", default="",
                       help=f"value for {f} column (optional micronutrient; blank if unknown)")
    args = p.parse_args()
    row = {f: getattr(args, f) for f in FIELDS}

    errs = validate_numeric(row)
    if errs:
        for e in errs:
            print(f"error: {e}", file=sys.stderr)
        return 1

    if not CSV_PATH.exists():
        print(f"Error: {CSV_PATH} not found", file=sys.stderr)
        return 1

    # r+ lets us read existing rows then seek-to-end for append, all under
    # one open file handle so the flock remains held across the entire
    # read-decide-append sequence.
    with open(CSV_PATH, "r+", newline="", encoding="utf-8") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.seek(0)
            # Skip a UTF-8 BOM (Excel-saved CSVs) so the first header isn't
            # misread. Can't open with utf-8-sig: its encoder would inject
            # a BOM mid-file on the append write below.
            if fh.read(1) != "\ufeff":
                fh.seek(0)
            reader = csv.DictReader(fh)
            for existing in reader:
                if (existing.get("food_name") == row["food_name"]
                        and existing.get("source") == row["source"]):
                    print(f"skipped (duplicate): {row['food_name']} from {row['source']}")
                    return 0
            # No duplicate — append at end.
            fh.seek(0, 2)  # seek to EOF
            writer = csv.DictWriter(fh, fieldnames=FIELDS)
            writer.writerow(row)
            print(f"appended: {row['food_name']} from {row['source']}")
            return 0
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


if __name__ == "__main__":
    sys.exit(main())
