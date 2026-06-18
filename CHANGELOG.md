# Changelog

## [v0.16.0] — 2026-06-18

### ✨ 新功能：三段碳循環（選用，預設仍二段）

- **`diet-targets.py` 新增 `--tiers`（2/3，預設 2、可由 `members.json` 的 `tiers` 設定）**：訓練強度有明顯分級者可開三段「高強度 / 中強度 / 休息」。中強度係數取高/低中點（recomp → 1.10 / 1.00 / 0.90）。蛋白質與脂肪三段固定釘體重，碳水獨自吸收熱量差＝碳水階梯。
- **`training_day` 欄位支援三值**：`TRUE`(高強度)／`mid`(中強度)／`FALSE`(休息)。`pal-from-log.py`、`weight-log-append.py` 把 `TRUE` 與 `mid` 都計入訓練頻率（中強度日也進 PAL）；`diet-summary.py` 新增 `mid-intensity day` 標籤。
- `AGENTS.md`（單人）與 `group/AGENTS.md`（多人）補「進階：三段碳循環」說明。

> 向後相容：預設仍二段；未設 `tiers` 的使用者／成員永不產生 `mid`、行為不變；舊 `TRUE`/`FALSE` 資料照常解析。

## [v0.15.0] — 2026-06-18

### ♻️ 結構：AGENTS.md 為單一來源（spec），CLAUDE.md = `@AGENTS.md`

- **canonical spec 從 `.claude/skills/diet-coach/SKILL.md` 移到根目錄 `AGENTS.md`**：Codex 原生讀取；同層新增 `CLAUDE.md`（一行 `@AGENTS.md`，Claude Code 展開 import）。兩種 provider 讀同一份來源、不再 drift。
- **移除 shipped `.claude/skills/diet-coach/SKILL.md`**：要裝成 `/diet-coach` skill 改為「複製 `AGENTS.md` → `~/.claude/skills/diet-coach/SKILL.md`」（`AGENTS.md` 開頭保留 skill frontmatter，複製即合法）。
- spec 內部自我引用改為檔名無關（「本檔」）；README 安裝步驟、檔案表、升級與 troubleshooting、badge 一併更新。
- `group/` 同步採同模式（`AGENTS.md` 為 spec、`CLAUDE.md` = `@AGENTS.md`），並補上估算原則／辨識陷阱段落。

> Migration：既有 skill 使用者重 pull template 後 `cp AGENTS.md ~/.claude/skills/diet-coach/SKILL.md`（先備份 backfill 過的個人資料）；工作目錄使用者把 `AGENTS.md` + `CLAUDE.md` 放進資料目錄即可。

## [v0.14.0] — 2026-06-16

### ✨ 新功能：食藥署鈣鐵回填 + food_reference 鈣鐵欄

- **food_reference.csv 新增 `calcium_mg,iron_mg` 兩欄**（選用，僅在來源提供時填，其餘留空不估算）。
- **新增 `scripts/backfill-food-ref-minerals.py`**：從食藥署食品營養成分資料庫 API（data.gov.tw dataset 8543 / InfoId=20）抽取鈣鐵（per 100g），依 `food_name` 比對回填 food_reference 的食藥署列。dry-run 預設、原子寫入、後綴模糊比對 fallback。本次回填 2096／2160 列（97%）。
- **`food-ref-append.py` 新增選用 `--calcium-mg` / `--iron-mg`**：不填則留空，向後相容（既有 8 參數呼叫不受影響）。
- 與 `diet_log` 的 `calcium_mg`/`iron_mg` 串接：詢問微量營養素是否足夠時，食物來源（diet_log）＋ 保健品（supplement_log）合併對照 DRI（見 SKILL.md「微量營養素參考值」）。

## [v0.13.0] — 2026-06-16

### ✨ 新功能：微量營養素參考值（DRI 對照）

- **SKILL.md（單人）與 `group/CLAUDE.md`（多人）新增「微量營養素參考值」章節**：成人每日建議攝取量（19-50 歲）對照表，含台灣衛福部 DRIs 第八版（2022）與美國 NASEM DRIs，涵蓋鈣／鐵／鋅／鎂與維生素 A/C/D/E/K/B 群／葉酸／菸鹼素。
- **新增選用紀錄檔 `supplement_log.csv`（多人版 `supplement_log_<slug>.csv`）**：欄位 `date,supplement,dose_mg,notes`，與 diet_log 的鈣鐵欄位合併判讀某微量營養素是否達 DRI。
- **diet_log 欄位擴充**：新增 `calcium_mg,iron_mg`（僅在食物有營養標示時填，不估算無標示值）。
- 定位為「被動參考」：不主動追蹤，僅在使用者主動詢問保健品／微量營養素是否足夠時引用；強調多樣化飲食優先、保健品為補充，不建議自行調整劑量或停用處方藥物。

## [v0.12.0] — 2026-06-16

### ✨ 新功能：全家便利商店食安 API 查詢工具

- **新增 `scripts/familymart-lookup.py`**：查詢[全家食在購安心](https://foodsafety.family.com.tw/Web_FFD_2022/)官方 API，取得商品完整標示值（P/C/F + 熱量 + 份量），自動 append 至 `food_reference.csv`。
  - 兩段式查詢：`QueryFsProductListByFilter`（關鍵字 → CMNO 清單）→ `QueryFsProductByItem`（CMNO → 完整 `NUTRIENTS`）
  - 支援關鍵字搜尋、CMNO 直查、`--list-only` 只列不寫、互動式多選
  - 寫入透過 `food-ref-append.py`（flock + dedupe 保護），race-safe
- **用法**：
  ```sh
  # 關鍵字搜尋（互動選擇要寫入哪幾項）
  python3 scripts/familymart-lookup.py "雞胸"
  # 直接用 CMNO 查並寫入
  python3 scripts/familymart-lookup.py --cmno 0357416
  # 只看結果不寫入
  python3 scripts/familymart-lookup.py "飯糰" --list-only
  ```

## [v0.11.1] — 2026-06-16

### 📊 新增：能量收支校正（recomp 合理性檢查）

- SKILL.md（單人）與 `group/CLAUDE.md`（群組）新增「能量收支校正」流程：量體重後，用窗內飲食＋訓練紀錄反推「實測體重/體脂變化是否合理」（平均每日攝取 − TDEE → 預測 Δ體重，對照實測 Δ體重/Δ體脂）。
- 內建誤差守則：攝取自估 ±15-20%、體脂量測噪訊 ±2-3%（單筆 Δ 落雜訊內即明說、看趨勢）；飲食缺記 > 30% 只做定性判讀、不給數字。

## [v0.11.0] — 2026-06-16

### ✨ 新功能：營養目標改「即時推導」+ recomp goal

- **新增 `scripts/diet-targets.py`**：營養目標不再寫死在 SKILL.md，改由「最新 TDEE（`weight_log` 最後一筆）＋ goal」即時推導訓練日/休息日二段式目標——量體重重算 TDEE 後目標自動更新，免手改。單人用 `--goal`、群組用 `--slug`（goal 讀 `members.json`）。
- **新增 `recomp` goal**（body recomposition）：訓練日 TDEE×1.10／休息日 ×0.90，熱量循環、週均 ≈ 維持體重——增肌減脂。完整 goal 選項：`cut` / `maintain` / `recomp` / `bulk`。
- **`group/members.example.json`** 加 `goal` 範例欄位。
- SKILL.md（單人）與 `group/CLAUDE.md`（群組）重算流程改為「量體重 → helper 寫入 → `diet-targets.py` 推導」，移除「手動算目標 ＋ 更新 SKILL.md 表格 ＋ 標版本日期」步驟。

## [v0.10.1] — 2026-06-15

### 文件 / 群組可用性
- README 群組設定加入 **`CTB_GROUP_AUTO_RESPOND=1`** 說明（bot 對群裡每則訊息免 @mention 回應）＋ privacy Disable 的「移出再加回群組」注意事項；diet-coach-bot 版本需求升到 ≥ `v1.6.6-diet.2`（含群組照片 caption @mention 偵測修正 ＋ 該 flag）。
- `group/CLAUDE.md` 加「何時回應（auto-respond 模式）」：只回食物/體重、純閒聊保持安靜。

## [v0.10.0] — 2026-06-15

### ✨ 新功能：多人問責群組模式 + 代謝體重追蹤

- **多人問責群組（group accountability）**：新增 `group/`（`CLAUDE.md` 多人版 spec、`members.example.json`、`AGENTS.md`、`WELCOME.md` onboarding 範本）。多名成員在同一個 Telegram 群組各記各的飲食、bot 公開估算、超標公開點名（羞恥心問責）。需搭配 [diet-coach-bot](https://github.com/didiowen/diet-coach-bot) ≥ `v1.6.6-diet.1`（提供群組 sender tag ＋ 防偽）；成員依驗證過的數字 `telegram_id` 歸人。
- **代謝體重追蹤**：新增 `scripts/weight-log-append.py`——回報體重/體脂時自動算 PAL（從 diet_log 訓練頻率）＋ BMR/TDEE（有體脂 Katch-McArdle、否則 Mifflin），原子（flock）append。單人寫 `weight_log.csv`、群組 `--slug` 寫 `weight_log_<slug>.csv`。

### ⚠️ Breaking：weight_log.csv schema 升級
- `weight_log.csv` 從 4 欄 `date,weight_kg,body_fat_pct,notes` → 8 欄 `date,height_cm,weight_kg,body_fat_pct,bmr,tdee,pal,notes`（仍在 0.x；schema-lock 承諾自 v1.x 起才生效）。
- **Migration**：既有 4 欄 weight_log——開一個新檔用 8 欄 header，舊資料用 `weight-log-append.py` 逐筆補回（自動算 BMR/TDEE/PAL）；或保留舊檔，但 SKILL.md 體重流程已改用新 helper / schema。
- SKILL.md「確認後動作」改為呼叫 `weight-log-append.py`（取代手動 append）。

## [v0.9.2] — 2026-06-15

### 改進

- **新增「工作目錄 CLAUDE.md」安裝模式**：README 安裝步驟改為兩種模式擇一——
  - 模式 A｜Skill：放進 `~/.claude/skills/diet-coach/SKILL.md`，用 `/diet-coach`（官方 MCP plugin 適用）
  - 模式 B｜工作目錄：把同一份 spec 放成 bot 工作目錄的 `CLAUDE.md`，Agent SDK 開機自動載入、免打 `/diet-coach`（ctb 等適用）
- canonical spec 仍是單一檔（`.claude/skills/diet-coach/SKILL.md`），兩模式共用同內容，避免雙檔 drift。檔案含 YAML frontmatter：當 SKILL.md 可註冊 skill，當 CLAUDE.md frontmatter 無害。
- `AGENTS.md` 改為指向「`CLAUDE.md` 或 `SKILL.md`（讀存在者）」，同時支援兩模式的 Codex 使用者。

### Migration

- 既有 Skill 安裝者不受影響，照舊可用。
- 想改工作目錄模式：把 spec 複製成 `<工作目錄>/CLAUDE.md`（見 README 安裝步驟模式 B）。

## [v0.9.1] — 2026-06-12

### 改進

- **撤回 symlink 推薦，全面改回 cp**：v0.9.0 的 symlink + auto-backfill 組合會把使用者個人資料寫進 template repo 並被 git 追蹤，升級時要先 commit/stash 才能 git pull——對非工程使用者太繞，容易放棄。改回單純的 `cp` 流程，README 不再列 trade-off 區塊。
- v0.9.0 的 repo 結構調整（SKILL.md 在 `.claude/skills/diet-coach/`）**保留**——對齊 Claude Code skill 目錄慣例，但安裝命令是純 `cp`。
- README 升級段：合併成單一 cp 流程（原本拆成 symlink / copy 兩條）。
- README Troubleshooting：移除 `readlink` symlink 驗證行。

### Migration

- 任何安裝者：照新 README 走純 `cp` 流程即可
- 已 v0.9.0 setup symlink 的使用者（如果有）：可以保留 symlink（仍然能跑），或 `rm + cp` 改回普通檔案

## [v0.9.0] — 2026-06-12

### 結構調整：SKILL.md 移到 `.claude/skills/diet-coach/SKILL.md`

讓 repo 直接對齊 Claude Code 的 skill 目錄慣例，使用者可以用 symlink 一次性掛到本機，未來 `git pull` 自動同步新版 SKILL.md，省去手動 `cp` 步驟。

### 改進

- **`SKILL.md` → `.claude/skills/diet-coach/SKILL.md`**：repo 結構直接對齊 Claude Code 慣用 layout
- **README 安裝步驟**：原本 `mkdir + cp` 改成 `ln -sfn` symlink。明示 trade-off（git pull 自動更新 vs. backfill 寫進 template repo 需處理 git 衝突）；提供 `cp` fallback
- **README 升級段**：分成 symlink 安裝者（先備份 SKILL.md → git pull → 解衝突）與 copy 安裝者（git pull → cp 覆蓋 → 手動 backfill）兩條路徑
- **檔案說明 table**：SKILL.md 路徑欄位同步更新
- **Troubleshooting**：「Claude session 沒讀到 skill」加 symlink 驗證指令 `readlink`

### Migration

- **既有 cp 安裝者**：不受影響，繼續用 cp 流程
- **想轉成 symlink**：先 `rm ~/.claude/skills/diet-coach/SKILL.md`（**先備份**！），再 `ln -sfn ~/diet-coach-template/.claude/skills/diet-coach ~/.claude/skills/diet-coach`
- **SKILL.md 內容本身不變**：行為規則、觸發條件、helper 呼叫等與 v0.8.0 完全相同

## [v0.8.0] — 2026-06-12

### 新功能：首次啟動自動 onboarding，不再需要手動編輯 SKILL.md

過去的安裝步驟最後一關卡在「自己打開 SKILL.md 把 `<your_gender>` 等 placeholder 換成實際資料」。對非工程背景的使用者是個明顯的 friction。

從這版起：

- **SKILL.md 加入觸發條件**：session 啟動時先檢查「使用者背景」段是否仍含 `<your_*>` placeholder。若是 → 進入初始設定流程；若否 → 直接進估算流程。
- **詢問流程明確化**：7 題（基本資料、體脂、訓練頻率、活動量、目標、飲食偏好、NG 上限），一次到位。
- **自動回填**：使用者回「確認」後，Claude 用 Edit 工具把 SKILL.md 的「使用者背景」段所有 `<your_*>` 與「NG 食物管理」段兩處 `<your_threshold>` 取代成實際值。
- **README 安裝步驟移除「手動編輯 SKILL.md」一條**，改成「第一次 DM bot：Claude 會問完並自動 backfill」。
- **README walkthrough 新增「首次 DM（自動 onboarding）」對話範例**，讓新使用者預期 bot 的首次互動樣貌。

### 為何重要

從技術 template 轉變成「裝完就能用」的工具——只需要複製檔案 + 設定 Telegram + DM bot 一次，全程不用打開 SKILL.md。這是 v1.0「外部使用者驗證」必要條件的鋪墊。

### Migration

- 既有使用者已手動填過 SKILL.md，不受影響（觸發條件偵測不到 placeholder → 不會重跑 onboarding）。
- 新使用者照新 README 安裝即可，不需要做任何 SKILL.md 改動。
- SKILL.md 位於全域 `~/.claude/skills/diet-coach/`，**不**會跟資料目錄一起同步——換機器時整個 `~/.claude/skills/diet-coach/` 一起搬過去。

## [v0.7.1] — 2026-06-12

### 改進（README tone polish + storage 概念修正）

- **README tagline / 功能 / 運作方式 / 注意事項 四段 tone 順過**：從「auto-estimates macros」這種 feature 描述改成 user-framed 框架（例：「記飲食三天就放棄的人專用」、「沒人會看到你昨天吃什麼」）。不動結構、安裝步驟、Telegram setup、Troubleshooting、Schema 鎖死宣告、walkthrough。
- **「自動重算 BMR/TDEE」段拿掉 "Mifflin-St Jeor" 公式名稱**：實際 helper script 內含兩套（有 body-fat-pct 用 Katch-McArdle、否則 fallback Mifflin-St Jeor），README 寫死單一公式會誤導。
- **運作方式 step 3 解綁 git**：原本「CSV append + 對照當日目標 + git commit/push」假設使用者一定走私有 git repo。改成 storage-agnostic 步驟 + 下方明列兩條儲存路徑：私有 git repo（自動 commit/push）或 Google Drive / iCloud / Dropbox 同步資料夾（OS 自動同步），並提示 Claude/Codex 可以幫忙設定。

### Migration

無 breaking change。純文件改動，helper scripts 與 CSV schema 不受影響。

## [v0.7.0] — 2026-06-12

### 新增（README 文件補完）

- **「第一日 walkthrough」**：mock Telegram 對話展示首次使用流程，讓新使用者能預期 bot 行為。
- **「升級」**：升級步驟（`git pull` template → 看 CHANGELOG → 同步 SKILL.md/scripts）+ semver 政策說明（patch/minor/major 各自承諾）。
- **「CSV schema 鎖死宣告」**：v1.x backward compat 承諾——既有欄位、順序、名稱、單位永不變動；只允許 append-only 新增可選欄位。v0.x 階段尚未承諾，要看 CHANGELOG migration 區段。
- **「Troubleshooting」**：6 個常見問題的修法（Claude 沒讀到 skill / Python missing / 權限 / CSV 不存在 / ctb bot 不回 / food-ref 寫不進）。

### 改進

- **CONTRIBUTING.md**：新增條目流程改為呼叫 `scripts/food-ref-append.py`，避免手動編輯 CSV 引起 race condition 與 escape bug。附使用範例與「為何不能手動編輯」說明。
- **README ctb option B Step 3**：補 `source .env`，原本省略會 silent 啟動失敗。
- **`pal-from-log.py` cosmetic**：印 `recommended PAL: 1.20` 而非 `1.2`，與 PAL 表 (`1.20 / 1.375 / 1.55 ...`) 風格一致。

### Migration

無 breaking change。既有使用者直接 `git pull` 套用文件改進；如有客製 CONTRIBUTING 流程請參考新範例。

## [v0.6.0] — 2026-06-12

### 新功能

- **`tests/` 資料夾 + pytest 測試套件**：4 支 helper 共 25 個測試案例（happy + error path），無外部依賴只用 stdlib + pytest。
  - `test_bmr_tdee.py`：Mifflin (男/女)、Katch-McArdle override、custom PAL、4 個 error path
  - `test_diet_summary.py`：訓練日／休息日／空 entries／missing file／bad date／missing columns
  - `test_pal_from_log.py`：normal recommendation、sparse warning、empty window 不 hard-output PAL、3 個 error path
  - `test_food_ref_append.py`：append、dedup、negative number、non-numeric、missing CSV
- **GitHub Actions CI workflow**（`.github/workflows/ci.yml`）：ubuntu-latest + macos-latest × Python 3.11 + 3.12（4 cell matrix），步驟為 checkout / setup-python / pip install pytest / py_compile / pytest。
- **README CI badge**：可一眼看到 main 是否綠燈。

### 為何重要

v0.5.0 引進 helper hardening 後，每個 release 都該證明 happy + error path 都不會 regress。在 PR 階段擋下 bug 比 release 後使用者回報快。

## [v0.5.1] — 2026-06-12

### 修正（critical — 公版裝完即壞的真實 bug）

- **新增 `weight_log.csv` 模板**：README 與 SKILL.md 一直 reference 它，但 repo 根本沒有這個檔；使用者跑體重追蹤流程會 file-not-found。
- **README 安裝步驟補完**：原本只說「複製 SKILL.md + 兩個 CSV」，缺了 `weight_log.csv` 模板、`scripts/` 整個資料夾、和明確的 `~/diet-coach/` 資料目錄建立步驟。SKILL.md 裡的 helper script 用 relative path `scripts/...`，使用者照舊版步驟裝完會 command-not-found。
- **SKILL.md helper path 統一**：4 支 helper 全部改為 `~/diet-coach/scripts/<helper>.py` 絕對形式（原本 BMR / diet-summary / pal-from-log 是 bare relative、food-ref-append 是絕對，3 vs 1 不一致）。

### 改進

- **SKILL.md NG `#(自訂)` placeholder** → `<your_threshold>`，並補一行說明用法，與其他 `<your_*>` 風格一致。
- **SKILL.md 重算流程 step 2**：原文「若缺則先詢問一次」會誤導——`bmr-tdee.py` `--gender` 是 argparse `required=True`，缺就直接 argparse 退；改為「先詢問使用者並補入『使用者背景』，再 invoke script」，並括號提醒不能跳過。

### Migration

- 既有自訂安裝者不受影響。新使用者照新 README 安裝。
- 既有客製 NG `#(自訂)` 仍可運作（Claude 自然語言解讀），但建議改為實際數字。

## [v0.5.0] — 2026-06-11

### 改進

- **Helper script 錯誤處理硬化**——四支 helper 遇到常見錯誤狀況不再噴 stack trace，改印人話 + `exit 1`，朝 v1.0 stability 推進：
  - **`bmr-tdee.py`**：semantic validation——weight 20–300 kg、height 100–250 cm、age 5–120、body-fat 3–60%、PAL 1.0–2.5；超出範圍直接拒絕
  - **`diet-summary.py`**：找不到 csv 印路徑 + hint；csv 缺欄位印缺哪些；`--date` 非 ISO 格式拒絕；當日 0 entries 印「當日無記錄」而非 0/0/0
  - **`pal-from-log.py`**：找不到 csv 印路徑 + hint；csv 缺欄位印缺哪些；`--today` 非 ISO 格式拒絕；`--days < 1` 拒絕；**window 內 0 個 entry 時不再硬輸出 `1.20 sedentary`**——改印 warning 並建議維持當前 PAL
  - **`food-ref-append.py`**：append 前驗證 `serving_size_g / calories / protein_g / carb_g / fat_g` 為非負 float，拒絕 NaN / 負數 / 非數字

### Migration

- 既有呼叫不受影響（exit code、stdout 格式不變；只多了 `stderr` 錯誤訊息）
- 邊角行為改變：`pal-from-log.py` 在空 window 時 `exit 0` 不再吐 `recommended PAL: 1.2`——上游程式若 grep `recommended PAL:` 抓建議值，現在會抓不到（這是預期行為，避免誤導）

## [v0.4.1] — 2026-06-11

### 新功能

- **`scripts/pal-from-log.py`**：從 `diet_log.csv` 過去 N 天訓練頻率推薦 PAL
  - 數視窗內 `training_day=TRUE` 的獨立日期，正規化為 sessions/week
  - 對照 Mifflin 標準 PAL 表（1.20 / 1.375 / 1.55 / 1.725 / 1.90）取一桶
  - 視窗內 < 3 個記錄日 → 印 sparse 警告

### 改進

- SKILL.md 體重追蹤「重算流程」第 1 步從手算 PAL 改為呼叫 `pal-from-log.py`；第 2 步將 `--pal` 改成必填（接收第 1 步推薦值），不再 fallback `[--NEW PAL]` 佔位
- 重算流程現在跟著訓練頻率自動調整 PAL，而非只用初始設定值

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
