# Agent instructions — diet-coach

The behavior spec for this directory is in `CLAUDE.md` (working-dir install) or `.claude/skills/diet-coach/SKILL.md` (skill install) — read whichever is present before responding to any food-related message.

- Identify food → consult `food_reference.csv` if relevant → estimate macros with sensible error bars → output CSV row(s) → append to `diet_log.csv` (see the spec's "Hard guard" for path verification).
- Language: 繁體中文 (zh-TW), Taiwanese conventions. Never PRC terminology.

This file exists because Codex (unlike Claude Code's Skill tool) does not auto-discover `.claude/skills/<name>/SKILL.md` or auto-load `CLAUDE.md`. Codex CLI's native discovery is `AGENTS.md`, so this file points it at the spec.
