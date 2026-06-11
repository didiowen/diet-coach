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


def calc_bmr(weight, height, age, gender, body_fat_pct=None):
    if body_fat_pct is not None:
        lbm = weight * (1 - body_fat_pct / 100)
        return round(370 + 21.6 * lbm), "Katch-McArdle"
    if gender == "female":
        return round(10 * weight + 6.25 * height - 5 * age - 161), "Mifflin-St Jeor (female)"
    return round(10 * weight + 6.25 * height - 5 * age + 5), "Mifflin-St Jeor (male)"


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

    bmr, formula = calc_bmr(args.weight, args.height, args.age, args.gender, args.body_fat_pct)
    tdee = round(bmr * args.pal)
    print(f"BMR: {bmr} kcal/day ({formula})")
    print(f"TDEE: {tdee} kcal/day (PAL {args.pal})")


if __name__ == "__main__":
    main()
