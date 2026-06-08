# Changelog

## [v0.2.0] — 2026-06-08

### 新功能

- **NG 食物管理**：7天內記錄超過3次甜點/蛋糕/挫冰/手搖飲等NG食物，自動觸發嚴厲嘲諷回應
- **BMR/TDEE 自動計算**：首次使用時詢問基本資料，以 Mifflin-St Jeor 公式計算 BMR × PAL，自動生成訓練日/休息日目標
- **食藥署台灣食品成分資料庫**：food_reference.csv 內建 2,160 筆通用食品資料（18分類，每100g，官方標示值）
- **眾包協作**：新增 CONTRIBUTING.md 與 PR template，開放社群貢獻品牌包裝食品資料

### 改進

- SKILL.md 通用化：移除個人資料，改為動態使用者設定流程
- 移除 Google Drive 依賴，改以本地 git 管理
- README.md 重寫為繁體中文，加入 BMR/TDEE 計算說明與 Telegram 6步驟設置教學
- skill name 改為 `diet-coach`

## [v0.1.0] — 2026-06-05

- 初始發佈：SKILL.md、diet_log.csv 模板、food_reference.csv 模板
- 支援台灣常見料理估算、便利商店食品辨識、訓練日/休息日二段式目標
- Telegram 照片傳送自動讀取營養標示
