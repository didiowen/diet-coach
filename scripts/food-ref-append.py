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
FIELDS = [
    "food_name", "source", "serving_size_g", "calories",
    "protein_g", "carb_g", "fat_g", "notes",
]


def main() -> int:
    p = argparse.ArgumentParser(
        description="Atomically append a row to food_reference.csv (flock + dedupe).",
    )
    for f in FIELDS:
        p.add_argument(f"--{f.replace('_', '-')}", required=True,
                       help=f"value for {f} column")
    args = p.parse_args()
    row = {f: getattr(args, f) for f in FIELDS}

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
