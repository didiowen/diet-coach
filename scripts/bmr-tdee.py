#!/usr/bin/env python3
"""BMR / TDEE calculator.

Picks formula based on inputs:
- body_fat_pct provided -> Katch-McArdle (370 + 21.6 * LBM); ignores gender
- otherwise              -> Mifflin-St Jeor (gender-dependent)

TDEE = BMR * PAL (default 1.55, moderate activity).

Example:
    bmr-tdee.py --weight 54.1 --height 156 --age 38 --gender female \\
        --body-fat-pct 30.4 --pal 1.55
"""
import argparse
import sys


def calc_bmr(weight, height, age, gender, body_fat_pct=None):
    if body_fat_pct is not None:
        lbm = weight * (1 - body_fat_pct / 100)
        return round(370 + 21.6 * lbm), "Katch-McArdle"
    if gender == "female":
        return round(10 * weight + 6.25 * height - 5 * age - 161), "Mifflin-St Jeor (female)"
    return round(10 * weight + 6.25 * height - 5 * age + 5), "Mifflin-St Jeor (male)"


def validate(args):
    errs = []
    if not (20 <= args.weight <= 300):
        errs.append(f"--weight {args.weight} out of range (expected 20-300 kg)")
    if not (100 <= args.height <= 250):
        errs.append(f"--height {args.height} out of range (expected 100-250 cm)")
    if not (5 <= args.age <= 120):
        errs.append(f"--age {args.age} out of range (expected 5-120)")
    if args.body_fat_pct is not None and not (3 <= args.body_fat_pct <= 60):
        errs.append(f"--body-fat-pct {args.body_fat_pct} out of range (expected 3-60)")
    if not (1.0 <= args.pal <= 2.5):
        errs.append(f"--pal {args.pal} out of range (expected 1.0-2.5)")
    return errs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weight", type=float, required=True, help="kg")
    ap.add_argument("--height", type=float, required=True, help="cm")
    ap.add_argument("--age", type=int, required=True)
    ap.add_argument("--gender", choices=["female", "male"], required=True)
    ap.add_argument("--body-fat-pct", type=float, default=None)
    ap.add_argument("--pal", type=float, default=1.55,
                    help="default 1.55 (moderate, 3-5 sessions/week)")
    args = ap.parse_args()

    errs = validate(args)
    if errs:
        for e in errs:
            print(f"error: {e}", file=sys.stderr)
        sys.exit(1)

    bmr, formula = calc_bmr(args.weight, args.height, args.age, args.gender, args.body_fat_pct)
    tdee = round(bmr * args.pal)
    print(f"BMR: {bmr} kcal/day ({formula})")
    print(f"TDEE: {tdee} kcal/day (PAL {args.pal})")


if __name__ == "__main__":
    main()
