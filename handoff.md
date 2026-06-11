# Diet-coach Handoff

## 2026-06-11 — v0.5.0 helper hardening

### Summary

- 四支 `scripts/*.py` 都把 stack trace 換成人話錯誤訊息 + `exit 1`；happy path 不變
- `pal-from-log.py` 空 window 不再硬吐 `1.20 sedentary`，改建議維持當前 PAL
- v0.5.0 是 v1.0 三大必要條件（外部驗證 / schema 鎖死 / migration note）的第一步

### Pending

- [ ] 找 1 名外部使用者從零跑通安裝 + 完成首次食物記錄 + 重算流程（v1.0 必要條件 #1）
- [ ] README 加 quickstart 截圖或 demo gif（v1.0 強烈建議）
- [ ] CONTRIBUTING.md 補 food_reference PR 實例（一張營養標示照 → PR 樣板）
- [ ] CSV schema 鎖死宣告（README 明寫「v1.x 不會新增/刪除欄位、不會改順序」）
- [ ] v0.x → v1.0 升級 migration note（例：舊版沒 weight_log.csv 要新建）

### Git

`4cb3be1 feat: harden helper scripts with friendly error messages (v0.5.0)` · `feat/helper-error-handling` · `Danube.local` · PR #5 open

### Next session

審 PR #5 → merge 後考慮先打 v0.5.0 release，再規劃 v1.0 roadmap。下一步 v0.5.1 可能是 README quickstart 截圖（最低成本提升 onboarding）。
