# diet-coach

A Claude Code skill for diet tracking via Telegram — estimates calories and macronutrients from food photos or text descriptions, and appends structured records to a local CSV.

## How it works

1. Send a food photo or text description to a Telegram bot connected to a Claude Code session
2. Claude reads `SKILL.md`, estimates nutrition (with uncertainty ranges), and asks for clarification when needed
3. The result is appended to `diet_log.csv` and committed to git

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | Claude Code skill spec — behaviour, targets, estimation rules |
| `diet_log.csv` | Template: per-meal nutrition log |
| `food_reference.csv` | Template: nutrition label database (auto-populated from photos) |

## CSV schema

**diet_log.csv**
```
date, meal_type, food, calories, protein_g, carb_g, fat_g, training_day, notes
```

**food_reference.csv**
```
food_name, source, serving_size_g, calories, protein_g, carb_g, fat_g, notes
```

## Setup

1. Place `SKILL.md` in `~/.claude/skills/diet-coach/SKILL.md`
2. Edit targets and user profile in `SKILL.md`
3. Create your local data directory (e.g. `~/diet-coach/` or inside a private repo)
4. Connect Claude Code to Telegram via the [telegram plugin](https://github.com/claude-plugins-official)
5. Send a food photo or description — Claude handles the rest

## Features

- Taiwanese cuisine focus (便當、自助餐、夜市、超商)
- Two-tier targets: training day vs rest day
- Auto-logs nutrition labels from photos → `food_reference.csv`
- Cooking method adjustments (stir-fry oil, deep-fry penalty, etc.)
- Uncertainty ranges, not false precision
