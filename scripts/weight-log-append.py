#!/usr/bin/env python3
"""Append a metabolic snapshot to a weight log (single-user or group).

Computes PAL (from recent training frequency in the diet log) and BMR/TDEE
(Katch-McArdle if body-fat given, else Mifflin-St Jeor), then atomically
(fcntl.flock) appends one row:

    date,height_cm,weight_kg,body_fat_pct,bmr,tdee,pal,notes

Modes:
  - single-user (no --slug): reads diet_log.csv, writes weight_log.csv.
    Provide profile (height/age/gender) via flags when body-fat is absent.
  - group (--slug NAME): reads diet_log_NAME.csv, writes weight_log_NAME.csv,
    and reads the member's profile from <dir>/members.json by slug.

Formulas mirror bmr-tdee.py and pal-from-log.py — keep the three in sync.

Examples:
    weight-log-append.py --weight 58.2 --body-fat-pct 24
    weight-log-append.py --slug alex --weight 70 --height-cm 178 --age 30 --gender male
"""
import argparse
import csv
import fcntl
import json
import sys
from datetime import date as date_cls, timedelta
from pathlib import Path

FIELDS = ["date", "height_cm", "weight_kg", "body_fat_pct", "bmr", "tdee", "pal", "notes"]


def calc_bmr(weight, height, age, gender, body_fat_pct=None):
    """Katch-McArdle when body fat is known (no gender needed), else Mifflin-St Jeor."""
    if body_fat_pct is not None:
        lbm = weight * (1 - body_fat_pct / 100)
        return round(370 + 21.6 * lbm)
    if gender == "female":
        return round(10 * weight + 6.25 * height - 5 * age - 161)
    return round(10 * weight + 6.25 * height - 5 * age + 5)


def bucket_pal(per_week):
    if per_week < 1.0:
        return 1.20
    if per_week < 3.0:
        return 1.375
    if per_week < 6.0:
        return 1.55
    if per_week < 8.0:
        return 1.725
    return 1.90


def pal_from_log(diet_log, today, days=14):
    """Bucketed PAL from unique training days in the past `days`. Defaults light if no log."""
    try:
        fh = open(diet_log, newline="")
    except FileNotFoundError:
        return 1.375
    window_start = today - timedelta(days=days - 1)
    training = set()
    with fh:
        for row in csv.DictReader(fh):
            try:
                d = date_cls.fromisoformat(row["date"])
            except (ValueError, KeyError):
                continue
            if window_start <= d <= today and row.get("training_day", "").strip().upper() in ("TRUE", "MID"):
                training.add(d)
    return bucket_pal(len(training) * 7 / days)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path.cwd()), help="working dir (default: cwd)")
    ap.add_argument("--slug", default=None, help="group member slug (omit for single-user)")
    ap.add_argument("--weight", type=float, required=True, help="kg")
    ap.add_argument("--body-fat-pct", type=float, default=None)
    ap.add_argument("--height-cm", type=float, default=None, help="profile; or from members.json")
    ap.add_argument("--age", type=int, default=None)
    ap.add_argument("--gender", choices=["female", "male"], default=None)
    ap.add_argument("--date", default=date_cls.today().isoformat())
    ap.add_argument("--notes", default="")
    args = ap.parse_args()

    base = Path(args.dir).expanduser()
    suffix = f"_{args.slug}" if args.slug else ""
    diet_log = base / f"diet_log{suffix}.csv"
    out = base / f"weight_log{suffix}.csv"

    # group mode: pull profile from members.json by slug
    prof = {}
    if args.slug:
        mfile = base / "members.json"
        if mfile.exists():
            try:
                for v in json.load(open(mfile)).values():
                    if isinstance(v, dict) and v.get("slug") == args.slug:
                        prof = v
                        break
            except (ValueError, OSError):
                pass
    height = args.height_cm if args.height_cm is not None else prof.get("height_cm")
    age = args.age if args.age is not None else prof.get("age")
    gender = args.gender or prof.get("gender")

    if not (20 <= args.weight <= 300):
        sys.exit(f"error: --weight {args.weight} out of range (20-300 kg)")
    if args.body_fat_pct is not None and not (3 <= args.body_fat_pct <= 60):
        sys.exit(f"error: --body-fat-pct {args.body_fat_pct} out of range (3-60)")
    if args.body_fat_pct is None and not (height and age and gender):
        who = f"member '{args.slug}'" if args.slug else "single-user"
        sys.exit(
            f"error: {who} has no body-fat-pct and an incomplete profile. "
            f"Provide --body-fat-pct, or height/age/gender (flags or members.json)."
        )

    try:
        today = date_cls.fromisoformat(args.date)
    except ValueError:
        sys.exit(f"error: --date {args.date!r} is not valid YYYY-MM-DD")

    pal = pal_from_log(diet_log, today)
    bmr = calc_bmr(args.weight, height or 0, age or 0, gender, args.body_fat_pct)
    tdee = round(bmr * pal)

    row = {
        "date": args.date,
        "height_cm": height if height else "",
        "weight_kg": args.weight,
        "body_fat_pct": args.body_fat_pct if args.body_fat_pct is not None else "",
        "bmr": bmr,
        "tdee": tdee,
        "pal": pal,
        "notes": args.notes,
    }

    with open(out, "a", newline="") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.seek(0, 2)
        if fh.tell() == 0:
            csv.writer(fh).writerow(FIELDS)
        csv.DictWriter(fh, fieldnames=FIELDS).writerow(row)
        fcntl.flock(fh, fcntl.LOCK_UN)

    label = args.slug or "self"
    print(f"OK {label}: weight={args.weight}kg bf={args.body_fat_pct} -> PAL={pal} BMR={bmr} TDEE={tdee}")


if __name__ == "__main__":
    main()
