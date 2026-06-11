# Changelog

## [v0.4.0] — 2026-06-11

### 新功能

- **`scripts/bmr-tdee.py`**：BMR/TDEE 計算 helper
  - 有 `--body-fat-pct` 自動用 **Katch-McArdle**（`370 + 21.6 × LBM`，不依性別、更準）
  - 否則 fallback **Mifflin-St Jeor**（依性別）
  - TDEE = BMR × PAL（預設 1.55，可用 `--pal` 覆寫）
- **`scripts/diet-summary.py`**：當日（或指定日期）累計 helper
  - 從 `diet_log.csv` grep 出指定日期條目、加總 kcal/P/C/F、附訓練日狀態
  - 預設讀取 `./diet_log.csv`，可用 `--csv` 覆寫

### 改進

- SKILL.md 「BMR / TDEE 計算」段落：公式表抽到 helper script，文件留下公式說明 + script 呼叫範例，更簡潔
- SKILL.md 估算流程新增 **Step 7：當日累計（按需）**，回答「今天還能吃多少」之類問題時直接呼叫 helper
- 所有 helper script 集中到 `scripts/` 資料夾（含既有的 `food-ref-append.py`）—— repo 根目錄維持 SKILL.md / README / CSV 模板的簡潔層次

## [v0.3.5] — 2026-06-10

### 改進

- SKILL.md 新增「使用者背景」與「營養目標」區塊的 placeholder 範例，讓首次使用者清楚知道需要填入哪些個人資料（性別、年齡、身高、體重、體脂、BMR、TDEE、訓練日/休息日目標等）
- 隱私保護：確保 public template 不含任何實際個人資料，所有數值均以 `<placeholder>` 形式呈現

## [v0.3.4] — 2026-06-10

### 改進

- README Telegram 設置改為兩方案並列：**選項 A — 官方 MCP plugin**（Claude Code 內建配對、單 chat） vs **選項 B — [ctb](https://github.com/htlin222/claude-telegram-bot)（社群方案）**（獨立進程、user allowlist、內建相片下載；多人共用 diet-coach 適用）
- 「建 BotFather Bot + 拿 user_id」抽成「共用前置需求」段落，讓兩方案的步驟更聚焦
- ctb 段落涵蓋 `npm install -g ctb`、`.env`（`TELEGRAM_BOT_TOKEN` + `TELEGRAM_ALLOWED_USERS`）、`cd <workdir> && ctb` 啟動；進階用法（多人 routing、`/cd`、相片下載）連結 upstream README

## [v0.3.3] — 2026-06-09

### 改進

- SKILL.md placeholder 統一化：移除 `<path-to>/diet_log.csv` 與 `<path-to>/food-ref-append.py` 兩處placeholder，改用一致的 `~/diet-coach/...` 形式
- 對 multi-tenant 部署（同機器跑多個 friend dir 例：`~/diet-coach-alex/`、`~/diet-coach-yu/`）更友善 — 一次 sed 替換即可全文 retarget

## [v0.3.2] — 2026-06-09

### 新功能

- **`food-ref-append.py`**：`fcntl.flock` + `(food_name, source)` dedupe 的 helper script，多人共用 bot 並發呼叫 race-free
  - CSV 路徑可用 env var `DIET_COACH_FOOD_REF` 覆蓋，預設為 `~/diet-coach/food_reference.csv`
  - Skip 重複品項（idempotent）；append 新品項
- SKILL.md「不需確認直接存入」改成指示 Claude 呼叫此 script，禁止用 Read+Write/Edit 直接編輯 food_reference.csv

### 改進

- 防止 lost-update：兩個 session 同時 read-modify-write 不會互相蓋掉

## [v0.3.1] — 2026-06-09

### 新功能

- **估算流程 Step 0：啟動時讀取當日紀錄（強制）** — 每次 session 啟動或收到新食物訊息時，先 grep 當天 diet_log.csv 條目，避免重複記錄、誤答「有沒有記過 X 餐」、或漏算累積總和

## [v0.3.0] — 2026-06-08

### 新功能

- **體重追蹤**：新增 `weight_log.csv`（date / weight_kg / body_fat_pct / notes）記錄歷次測量
- **2週提醒機制**：每次記錄食物時自動檢查上次量體重距今天數，≥14天在回覆末尾提醒
- **目標自動重算**：傳送體重/體脂數字即觸發 Mifflin-St Jeor 重算，顯示確認摘要後才寫入
- **使用者檔案完整化**：首次回報體重時詢問身高與年齡，補入 SKILL.md，之後不再詢問

### 改進

- 移除「熱量目標另開對話調整」的過時說明，目標調整已整合進體重追蹤流程

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
