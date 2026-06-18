#!/usr/bin/env python3
"""Derive nutrition targets (2-tier train/rest, or 3-tier high/mid/rest) for a member.

Targets are DERIVED, never stored: reads the member's latest TDEE + weight from
weight_log_<slug>.csv (group) or weight_log.csv (single-user) and a goal
(cut/maintain/bulk), then prints training-day and rest-day kcal + protein/carb/fat.
Because they're derived, they auto-update whenever a new weigh-in recomputes TDEE.

Goal factors applied to TDEE (training-day / rest-day):
  cut:      0.90 / 0.80   (~10% / ~20% deficit; weekly ~-15%)
  maintain: 1.00 / 1.00
  recomp:   1.10 / 0.90   (calorie cycling around maintenance; weekly ~net,
                           training-day surplus + rest-day deficit for body recomp)
  bulk:     1.10 / 1.00

3-tier mode (--tiers 3, or members.json "tiers": 3) inserts a mid-intensity day at
the midpoint factor (high+rest)/2 — e.g. recomp -> 1.10 / 1.00 / 0.90. Because protein
and fat are pinned to bodyweight, only the kcal factor moves and carbs absorb the swing.
Default stays 2-tier so existing single-/multi-user setups are unaffected.

Macros: protein 2.0-2.2 g/kg; fat 0.8-1.0 g/kg; carb fills the remainder.
Goal/tiers come from members.json unless --goal/--tiers override; defaults cut / 2.

Example:
    diet-targets.py --dir ~/diet-group --slug yr
    diet-targets.py --dir ~/diet-coach          # single-user
"""
import argparse
import csv
import json
import sys
from pathlib import Path

GOAL_FACTORS = {"cut": (0.90, 0.80), "maintain": (1.00, 1.00), "recomp": (1.10, 0.90), "bulk": (1.10, 1.00)}


def latest_weight_tdee(path):
    try:
        with open(path, newline="") as f:
            rows = list(csv.DictReader(f))
    except FileNotFoundError:
        return None, None
    if not rows:
        return None, None
    last = rows[-1]
    try:
        return float(last["weight_kg"]), float(last["tdee"])
    except (KeyError, ValueError):
        return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=str(Path.cwd()))
    ap.add_argument("--slug", default=None, help="group member slug (omit for single-user)")
    ap.add_argument("--goal", choices=list(GOAL_FACTORS), default=None, help="override members.json")
    ap.add_argument("--tiers", type=int, choices=[2, 3], default=None,
                    help="2-tier (train/rest) or 3-tier (high/mid/rest); default from members.json or 2")
    args = ap.parse_args()

    base = Path(args.dir).expanduser()
    suffix = f"_{args.slug}" if args.slug else ""

    goal, tiers = args.goal, args.tiers
    if (goal is None or tiers is None) and args.slug:
        mfile = base / "members.json"
        if mfile.exists():
            try:
                for v in json.load(open(mfile)).values():
                    if isinstance(v, dict) and v.get("slug") == args.slug:
                        if goal is None:
                            goal = v.get("goal")
                        if tiers is None:
                            tiers = v.get("tiers")
                        break
            except (ValueError, OSError):
                pass
    goal = goal or "cut"
    tiers = tiers if tiers in (2, 3) else 2

    weight, tdee = latest_weight_tdee(base / f"weight_log{suffix}.csv")
    if weight is None or tdee is None:
        sys.exit("error: no usable weight_log row (need weight_kg + tdee) — log a weigh-in first.")

    tf, rf = GOAL_FACTORS[goal]
    p_lo, p_hi = round(weight * 2.0), round(weight * 2.2)
    f_lo, f_hi = round(weight * 0.8), round(weight * 1.0)
    p_mid, f_mid = (p_lo + p_hi) / 2, (f_lo + f_hi) / 2

    def line(label, factor):
        kcal = round(tdee * factor)
        carb = max(0, round((kcal - p_mid * 4 - f_mid * 9) / 4))
        return f"{label}：熱量 {kcal}｜P {p_lo}-{p_hi} g｜C ~{carb} g｜F {f_lo}-{f_hi} g"

    print(f"goal={goal} | TDEE={round(tdee)} | weight={weight}kg | tiers={tiers}")
    if tiers == 3:
        print(line("高強度日", tf))
        print(line("中強度日", (tf + rf) / 2))
        print(line("休息日", rf))
    else:
        print(line("訓練日", tf))
        print(line("休息日", rf))


if __name__ == "__main__":
    main()
