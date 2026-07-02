#!/usr/bin/env python3
"""
backfill-food-ref-minerals.py — fill calcium_mg / iron_mg in food_reference.csv
from the Taiwan FDA food composition database (食藥署食品營養成分資料庫).

The 食藥署 rows in food_reference.csv are stored per-100g (serving_size_g=100),
matching the FDA DB's "每100克含量", so calcium/iron are copied directly with no
scaling. Non-食藥署 rows (packaged/restaurant items) are left blank — fill those
from a label when available.

Source: data.gov.tw dataset 8543 (InfoId=20), JSON-in-ZIP, long format
(one row per food × analysis item). We extract the 鈣 / 鐵 (minerals, mg/100g)
items and join to food_reference by food_name == 樣品名稱.

Dry-run by default (prints a preview). Pass --apply to rewrite the file.

Usage:
  python3 backfill-food-ref-minerals.py            # preview only
  python3 backfill-food-ref-minerals.py --apply    # write changes
  python3 backfill-food-ref-minerals.py --apply --csv /path/to/food_reference.csv
"""

import argparse
import csv
import fcntl
import io
import json
import os
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

FDA_URL = ("https://data.fda.gov.tw/opendata/exportDataList.do"
           "?method=ExportData&InfoId=20&logType=5")
CACHE = Path("/tmp/tfnd_20_5.json")
TFDA_SOURCE = "食藥署台灣食品成分資料庫"
DEFAULT_CSV = Path.home() / "diet-coach" / "food_reference.csv"
NEW_COLS = ["calcium_mg", "iron_mg"]


def load_fda_minerals() -> dict:
    """Return {樣品名稱: {'calcium_mg': str, 'iron_mg': str}} (per 100g, mg)."""
    if CACHE.exists() and CACHE.stat().st_size > 0:
        raw = CACHE.read_bytes()
    else:
        print(f"downloading FDA food composition DB … ({FDA_URL})", file=sys.stderr)
        req = urllib.request.Request(FDA_URL, headers={"User-Agent": "Mozilla/5.0"})
        zipped = urllib.request.urlopen(req, timeout=180).read()
        raw = zipfile.ZipFile(io.BytesIO(zipped)).read("20_5.json")
        CACHE.write_bytes(raw)
    data = json.loads(raw.decode("utf-8-sig"))
    out: dict = {}
    field = {"鈣": "calcium_mg", "鐵": "iron_mg"}
    for row in data:
        col = field.get(row.get("分析項"))
        if not col:
            continue
        name = row.get("樣品名稱")
        val = (row.get("每100克含量") or "").strip()
        try:
            num = float(val)
        except ValueError:
            continue  # "Tr"/"-"/blank → leave unknown
        out.setdefault(name, {})[col] = f"{num:g}"
    return out


def strip_suffix(name: str) -> str:
    """Drop trailing parenthetical annotations, e.g. '小米(2025年取樣)' → '小米'."""
    return re.sub(r"[（(][^（）()]*[）)]\s*$", "", name).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", type=Path,
                    default=Path(os.environ.get("DIET_COACH_FOOD_REF", DEFAULT_CSV)))
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = ap.parse_args()

    if not args.csv.exists():
        print(f"Error: {args.csv} not found", file=sys.stderr)
        return 1

    minerals = load_fda_minerals()
    print(f"FDA DB: {len(minerals)} foods with calcium/iron", file=sys.stderr)

    with open(args.csv, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        in_cols = reader.fieldnames or []

    out_cols = in_cols + [c for c in NEW_COLS if c not in in_cols]

    filled = exact = fuzzy = missed = skipped_nontfda = already = 0
    miss_examples = []
    for r in rows:
        for c in NEW_COLS:
            r.setdefault(c, "")
        if r.get("source") != TFDA_SOURCE:
            skipped_nontfda += 1
            continue
        if r.get("calcium_mg") and r.get("iron_mg"):
            already += 1
            continue
        name = r["food_name"]
        m = minerals.get(name)
        if m:
            exact += 1
        else:
            m = minerals.get(strip_suffix(name))
            if m:
                fuzzy += 1
        if m:
            if m.get("calcium_mg"):
                r["calcium_mg"] = m["calcium_mg"]
            if m.get("iron_mg"):
                r["iron_mg"] = m["iron_mg"]
            filled += 1
        else:
            missed += 1
            if len(miss_examples) < 12:
                miss_examples.append(name)

    print("\n=== backfill preview ===")
    print(f"  total rows           : {len(rows)}")
    print(f"  食藥署 rows filled    : {filled}  (exact {exact}, suffix-fuzzy {fuzzy})")
    print(f"  食藥署 already filled : {already}")
    print(f"  食藥署 unmatched      : {missed}")
    print(f"  non-食藥署 untouched  : {skipped_nontfda}")
    print(f"  unmatched examples    : {miss_examples}")

    if not args.apply:
        print("\n(dry-run — re-run with --apply to write)")
        return 0

    tmp = args.csv.with_suffix(".csv.tmp")
    with open(args.csv, "r+", encoding="utf-8") as lockfh:
        fcntl.flock(lockfh.fileno(), fcntl.LOCK_EX)
        try:
            with open(tmp, "w", newline="", encoding="utf-8") as out:
                w = csv.DictWriter(out, fieldnames=out_cols)
                w.writeheader()
                for r in rows:
                    w.writerow({c: r.get(c, "") for c in out_cols})
            os.replace(tmp, args.csv)
        finally:
            fcntl.flock(lockfh.fileno(), fcntl.LOCK_UN)
    print(f"\napplied → {args.csv} (now {len(out_cols)} columns)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
