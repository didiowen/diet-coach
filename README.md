# 飲食教練

[![CI](https://github.com/didiowen/diet-coach/actions/workflows/ci.yml/badge.svg)](https://github.com/didiowen/diet-coach/actions/workflows/ci.yml)
[![Made in Taiwan](https://img.shields.io/badge/Made%20in-Taiwan%20%F0%9F%87%B9%F0%9F%87%BC-red)](https://github.com/htlin222/society-calendar)
[![Claude Code](https://img.shields.io/badge/Claude%20%2B%20Codex-AGENTS.md-blueviolet?logo=anthropic)](https://claude.ai/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一個用 Telegram 跟 Claude 對話的飲食日記。傳張食物照片或文字描述，bot 幫你估熱量與蛋白質／碳水／脂肪，寫進本地 CSV——記飲食三天就放棄的人專用。

## 功能

- 認得台灣食物——便當、自助餐、夜市、超商，不是只懂 western salad
- 訓練日與休息日分開設目標，跟你練的節奏一致
- 傳一張包裝營養標示照，自動累積進 `food_reference.csv`
- 烹調方式（炒油、油炸、勾芡）會算進熱量誤差
- 給範圍，不給假精確值——±15–20% 是誠實
- NG 食物（甜點、手搖飲）超過你設的週上限，bot 會嚴厲嘲諷
- 兩週沒量體重就提醒，回報後自動重算 BMR/TDEE，確認後更新目標

## 運作方式

1. Telegram DM 傳食物照片或文字描述
2. Claude / Codex 讀取 spec（canonical 是 `AGENTS.md`；Claude 經同層 `CLAUDE.md` 的 `@AGENTS.md` import），估算營養素並主動問清楚（油量、份量、醬料）
3. CSV append + 對照當日目標

儲存方式擇一：

- **私有 git repo**：CSV 寫入後 `git add → commit → push`
- **Google Drive / iCloud / Dropbox 等同步資料夾**：把資料夾路徑指向掛載點，作業系統自動同步，不用 git

兩種都行——關鍵是 spec 裡的 CSV 路徑指對位置。實際要怎麼跑 Claude/Codex 可以幫你設。

想看實際對話的樣子，跳到 [第一日 walkthrough](#第一日-walkthrough)。

## 檔案說明

| 檔案 | 用途 |
|------|------|
| `AGENTS.md` | **canonical spec**——行為規則、目標、估算原則（Codex 原生讀）。開頭含 skill frontmatter，複製成 `SKILL.md` 即可裝成 skill（`/diet-coach`），見[安裝步驟](#安裝步驟) |
| `CLAUDE.md` | 一行 `@AGENTS.md`——讓 Claude Code（工作目錄模式）展開 import、讀到同一份 spec |
| `diet_log.csv` | 模板：逐餐營養記錄 |
| `food_reference.csv` | 模板：食品資料庫（可從照片自動累積；公版內建台灣食藥署 2,160 筆） |
| `weight_log.csv` | 模板：體重/代謝快照（8 欄：`date,height_cm,weight_kg,body_fat_pct,bmr,tdee,pal,notes`） |
| `scripts/bmr-tdee.py` | BMR/TDEE 計算（Katch-McArdle 或 Mifflin-St Jeor） |
| `scripts/diet-summary.py` | 當日累計 kcal/P/C/F 從 `diet_log.csv` 加總 |
| `scripts/pal-from-log.py` | 從 `diet_log.csv` 過去 N 天訓練頻率推薦 PAL |
| `scripts/food-ref-append.py` | 並發安全 append `food_reference.csv`（`fcntl.flock` + dedupe） |
| `scripts/weight-log-append.py` | 算 PAL+BMR/TDEE 並原子 append `weight_log.csv`（單人）或 `weight_log_<slug>.csv`（群組） |
| `group/` | 多人問責群組模板：`CLAUDE.md`、`members.example.json`、`AGENTS.md`、`WELCOME.md`（見[多人問責群組模式](#多人問責群組模式group-accountability)） |

## CSV 欄位

**diet_log.csv**
```
date, meal_type, food, calories, protein_g, carb_g, fat_g, training_day, notes
```

**food_reference.csv**
```
food_name, source, serving_size_g, calories, protein_g, carb_g, fat_g, notes
```

## 安裝步驟

```bash
# 1. Clone 本 repo（拿模板和 helper 腳本）
git clone https://github.com/didiowen/diet-coach.git ~/diet-coach-template

# 2. 建立個人資料目錄（建議放私有 git repo 或 Google Drive，含個人健康資料）
mkdir -p ~/diet-coach

# 3. 複製模板與 helpers 到個人資料目錄
cp ~/diet-coach-template/diet_log.csv ~/diet-coach/
cp ~/diet-coach-template/weight_log.csv ~/diet-coach/
cp ~/diet-coach-template/food_reference.csv ~/diet-coach/
cp -r ~/diet-coach-template/scripts ~/diet-coach/

# 4. 安裝 spec —— canonical 是 AGENTS.md；同層的 CLAUDE.md 只是一行 @AGENTS.md
#    （Codex 原生讀 AGENTS.md；Claude Code 讀 CLAUDE.md 並展開 import——兩邊同一份來源）

#   模式 B｜工作目錄（ctb 等 Agent SDK，開機自動載入、推薦）：把 spec 放進 bot 工作目錄
cp ~/diet-coach-template/AGENTS.md ~/diet-coach/AGENTS.md
cp ~/diet-coach-template/CLAUDE.md ~/diet-coach/CLAUDE.md   # 一行 @AGENTS.md

#   模式 A｜Skill（想用 /diet-coach）：把同一份 spec 複製成 SKILL.md
#   （AGENTS.md 開頭已含 skill 需要的 YAML frontmatter，複製即為合法 skill）
mkdir -p ~/.claude/skills/diet-coach
cp ~/diet-coach-template/AGENTS.md ~/.claude/skills/diet-coach/SKILL.md
```

5. 設定 Telegram（見下方教學）
6. 第一次 DM bot：Claude 會逐項詢問身高、體重、體脂、目標等，回完自動 backfill 到你的 spec 檔（`AGENTS.md`；skill 模式則為 `SKILL.md`）。**不需要手動編輯**。
7. 之後傳食物照片或描述，Claude 直接估算記錄

> spec 檔（`AGENTS.md`）內預設的資料目錄是 `~/diet-coach/`。若你用其他位置（例：`~/Dropbox/diet-coach/`），請全文搜尋取代為你的實際路徑。

## Telegram 設置

> 官方 plugin 完整教學：[Claude Code Telegram 快速設置](https://abmedia.io/claude-code-telegram-quick-setup)

兩種設置方案，擇一即可：

- **選項 A — 官方 MCP plugin**：安裝最簡單、Claude Code session 內配對；適合單一 chat、單一工作目錄
- **選項 B — [ctb](https://github.com/htlin222/claude-telegram-bot) (社群方案)**：獨立進程，內建 user allowlist、相片下載；可在不同 chat 共用同一個 bot 路由到不同目錄（多人共用 diet-coach 適用）

### 共用前置需求

- 已建立 Telegram Bot：DM [@BotFather](https://t.me/botfather)、`/newbot`、依提示完成、取得 Token（格式 `123456789:AAH...`）
- 知道自己的 Telegram user_id：DM [@userinfobot](https://t.me/userinfobot)（選項 B 的 allowlist 必須）

### 選項 A — 官方 MCP plugin

需求：已安裝 Claude Code（`claude` 指令）與 [Bun](https://bun.sh)（`curl -fsSL https://bun.sh/install | bash`）。

**Step 1 — 安裝插件**

進入 Claude Code session，執行：
```
/plugin install telegram@claude-plugins-official
/reload-plugins
```

**Step 2 — 設定 Token**

```
/telegram:configure 你的_BOT_TOKEN
```

**Step 3 — 以 Channels 模式重啟**

```bash
claude --channels plugin:telegram@claude-plugins-official
```

> 注意：必須加 `--channels` 參數，Bot 才會上線；單獨執行 `claude` 不會收到訊息。

**Step 4 — 配對**

1. Telegram 傳任意訊息給 Bot → 收到 6 字元配對碼
2. 回到 Claude Code session，執行：`/telegram:access pair <配對碼>`
3. 確認提示選 **Yes**

**Step 5 — 鎖定存取**

```
/telegram:access policy allowlist
```

### 選項 B — ctb (社群方案)

需求：Node.js + npm。

**Step 1 — 安裝**

```bash
npm install -g ctb
```

**Step 2 — 設定 .env**

在你的 diet-coach 工作目錄（例如 `~/diet-coach/`）建立 `.env`：

```
TELEGRAM_BOT_TOKEN=你的_BOT_TOKEN
TELEGRAM_ALLOWED_USERS=你的_user_id
```

> `TELEGRAM_ALLOWED_USERS` 是逗號分隔的 user_id 清單；不設則任何人都能 DM bot，不建議。

**Step 3 — 啟動**

```bash
cd ~/diet-coach && source .env && ctb
```

> 必須 `source .env`，ctb 才會讀到 `TELEGRAM_BOT_TOKEN`；省略會啟動失敗或 silent。

Bot 上線後 DM 它即可。ctb 把訊息路由到啟動時的工作目錄，並自動把相片下載成本地檔案路徑供 Claude 或 Codex 讀取；無需另外設定相片處理。

**（選用）改用 Codex / ChatGPT 免費額度**

ctb 內建 `claude` 與 `codex` 兩個 provider。如果想省 Claude token，可改走 ChatGPT 帳號的免費 Codex 額度：

1. 先在 terminal 跑一次 `codex` CLI 完成 OAuth（產出 `~/.codex/auth.json`）— 詳見 [openai/codex](https://github.com/openai/codex)
2. ctb 啟動後 DM bot 打 `/provider codex` 切換

注意：diet-coach 的 prompt 都在 Claude 上調校，Codex（GPT-5.x）的食物估算與 zh-TW 輸出品質請自行實測。

**（進階）改裝 diet-coach-bot fork**

想拿到較新的 Claude model IDs（haiku-4-5、sonnet-4-6、opus-4-7；upstream 還是 haiku-3-5 → 已退役）與 `ALLOWED_PATHS` `~` expansion bug fix，可改裝本專案專屬的 ctb fork：

```bash
npm install -g github:didiowen/diet-coach-bot
```

其餘用法與 upstream 完全相同。差異詳見 [diet-coach-bot README](https://github.com/didiowen/diet-coach-bot)。

ctb 進階用法（多人 allowlist 各自 routing、`/cd` 切換工作目錄、相片下載等）詳見 [htlin222/claude-telegram-bot](https://github.com/htlin222/claude-telegram-bot) README。

## 個人化設定

在 spec（`AGENTS.md`）中調整以下區塊：

- **初始設定**：首次使用時 Claude 或 Codex 會詢問基本資料，自動計算 BMR/TDEE 並設定目標
- **NG食物管理**：定義哪些食物算 NG、每週限制次數、超標時的回應風格

## 第一日 walkthrough

### 首次 DM（自動 onboarding）

```
You: 哈囉
Bot: 看起來是第一次用我，先建立你的使用者背景：
     1) 性別、年齡、身高、體重？
     2) 有體脂數字嗎？（沒有也可以）
     3) 每週幾次重訓或有氧？
     4) 日常活動量？（久坐/輕度/中度/重度）
     5) 目標？（減脂/增肌/維持）
     6) 飲食偏好或過敏？
     7) NG 食物（甜點、手搖飲）週上限？建議 3 次

You: 女 38 156 54；體脂 30；訓練 3次/週；中度；減脂；低脂高蛋白；3 次

Bot: 算好了——
     使用者背景已建立：
     - F/38/156｜54 kg｜體脂 30%
     - BMR 1186（Katch-McArdle）｜TDEE 1838（PAL 1.55）
     - 目標：減脂
     - 訓練日：熱量 1700｜P 115-125｜C 200-220｜F 55-60
     - 休息日：熱量 1500｜P 115-125｜C 130-150｜F 55-60
     - NG 上限：3 次/週
     回覆「確認」即寫入 spec。

You: 確認

Bot: 已建立。往後傳食物照片或描述直接記錄。
```

### 開始記錄

```
You: 早上吃了一碗燕麥配蛋白粉、兩顆蛋
Bot: 你今天是訓練日還是休息日？
You: 訓練日
Bot: 估算結果（誤差 ±15-20%）
     - 燕麥 50g：~190 kcal｜P 7g｜C 35g｜F 3g
     - 蛋白粉 30g：~120 kcal｜P 25g｜C 3g｜F 1.5g
     - 雞蛋 ×2：~140 kcal｜P 12g｜C 1g｜F 10g
     - 合計：~450 kcal｜P 44g｜C 39g｜F 14.5g

     已 append 到 diet_log.csv。
     當日累計：450 / 1700 kcal（訓練日目標）— 26%
```

之後每餐傳照片或文字描述，bot 自動估算 + append。每兩週若沒回報體重，會在回覆末尾提醒。

回報體重時（例：「體重 54.5 體脂 22」）會觸發 BMR/TDEE 重算，顯示確認摘要等你回「確認」才寫入。

## 多人問責群組模式（group accountability）

想用「群體力量＋羞恥心」做飲食控制？把多名成員放進同一個 Telegram 群組，bot 各自估算、各記各的檔，超標就在群裡「公開點名」。

**需求**：用 [diet-coach-bot](https://github.com/didiowen/diet-coach-bot)（≥ `v1.6.6-diet.2`）跑——它會把群組訊息自動標上發話者（`[group message from <name> (telegram_id:<id>)]`），多人版 spec 才能把每則食物歸到正確的人；身分以驗證過的數字 `telegram_id` 為準、有防偽（避免成員互相栽贓）。

**設定**：
1. 建一個群組工作目錄（例 `~/diet-group/`），把 `group/CLAUDE.md` 放成它的 `CLAUDE.md`。（可選）把 `group/WELCOME.md` 放成工作目錄的 `WELCOME.md`——新成員第一次傳訊息時 bot 會 verbatim 貼出來當 onboarding／公開揭露（記得改最後一行的管理員聯絡方式）。
2. `cp group/members.example.json ~/diet-group/members.json`，填入每位成員的 `telegram_id` → `slug` / `name` /（可選）`height_cm`/`age`/`gender`。
3. 每位成員建 `diet_log_<slug>.csv` 與 `weight_log_<slug>.csv`（header 同單人版 / 8 欄）；把 `scripts/` 複製或指過去。
4. 在那個工作目錄跑 diet-coach-bot 的 `.env`：新 bot token、`TELEGRAM_ALLOWED_USERS` 含全體成員 user_id、`ALLOWED_PATHS` 含工作目錄，並設 **`CTB_GROUP_AUTO_RESPOND=1`**（讓 bot 對群裡「每則訊息」都回、免 @mention；配合多人版 spec「只回食物/體重、純閒聊保持安靜」。接受 `1`/`true`/`yes`）。
5. BotFather `/setprivacy` → **Disable**（否則群裡沒 @ 的訊息根本不會送到 bot；改完要把 bot「移出再加回」群組才生效），再建 Telegram 群組把 bot ＋ 成員拉進去。

> 「沒 @ 也能丟照片就記」需要三件事到齊：① privacy **Disable**（bot 收得到訊息）② **`CTB_GROUP_AUTO_RESPOND=1`**（免 @ 回應）③ diet-coach-bot ≥ `v1.6.6-diet.2`（照片 caption 的 @mention 偵測 ＋ 上述 flag）。

成員傳食物 → bot 公開估算 ＋ 寫各自的檔；連續 NG（預設 7 天 >5 次）→ 群裡公開嘲諷那個人。體重回報 → `weight-log-append.py --slug <slug>` 記代謝快照。

> 隱私提醒：群組模式「刻意公開」彼此的飲食（這就是問責機制）。只把信任、同意被公開的人放進去。

## 升級

```bash
# 1. 拉取最新 template
cd ~/diet-coach-template && git pull origin main

# 2. 看 CHANGELOG 找 Migration 區段
less CHANGELOG.md

# 3. 同步 spec（先備份 backfill 過的個人資料）
cp ~/diet-coach/AGENTS.md /tmp/AGENTS.md.backup
cp ~/diet-coach-template/AGENTS.md ~/diet-coach/AGENTS.md
# 手動把備份裡的「使用者背景」與「NG 食物閾值」貼回新 AGENTS.md
# （skill 模式：再 cp ~/diet-coach-template/AGENTS.md ~/.claude/skills/diet-coach/SKILL.md）

# 4. 同步 helpers（無個人資料，直接覆蓋）
cp -r ~/diet-coach-template/scripts ~/diet-coach/
```

**Semver 政策**：

- **patch（0.x.y → 0.x.y+1）**：bug fix 或 helper error 訊息改善，**不破壞**呼叫介面與 CSV 欄位
- **minor（0.x → 0.x+1）**：新功能、helper 新增、SKILL.md 結構調整；可能新增 CSV 欄位但**不刪除既有欄位**
- **major（0 → 1）**：穩定承諾——CSV schema 鎖死（見下節）

升級後若 helper 跑不動，先看 [Troubleshooting](#troubleshooting)。

## CSV schema 鎖死宣告（v1.x backward compat 承諾）

從 **v1.0** 起，下列欄位順序與名稱在所有 v1.x release 都**不會變動**：

**diet_log.csv**
```
date, meal_type, food, calories, protein_g, carb_g, fat_g, training_day, notes
```

**food_reference.csv**
```
food_name, source, serving_size_g, calories, protein_g, carb_g, fat_g, notes
```

**weight_log.csv**
```
date, height_cm, weight_kg, body_fat_pct, bmr, tdee, pal, notes
```

v1.x 可以新增可選欄位（append-only），但**不會**：
- 刪除既有欄位
- 改變欄位順序
- 改變欄位名稱
- 改變單位（kg / cm / kcal / g）

需要破壞性 schema 變更時，會升 **v2.0** 並提供 migration script。在那之前你的 diet_log.csv 永遠可以被讀。

> v0.x 階段尚未做此承諾——v0.x 升級時請看 CHANGELOG 的 Migration 區段。

## Troubleshooting

### Claude / Codex 沒讀到 spec
- 工作目錄模式：確認 bot 工作目錄（`~/diet-coach/`）有 `AGENTS.md`（Codex 讀）與 `CLAUDE.md`（= `@AGENTS.md`，Claude 讀）
- skill 模式：確認 `~/.claude/skills/diet-coach/SKILL.md` 存在（從 template 的 `AGENTS.md` 複製而來）
- 重啟 Claude Code session（spec 是 session 啟動時載入）
- ctb 啟動時印的工作目錄是否為 `~/diet-coach`？若否，`cd ~/diet-coach && ctb`

### `python3: command not found`
- macOS: `brew install python@3.12`
- Linux: `sudo apt install python3` 或 `sudo dnf install python3`
- 確認版本：`python3 --version` 需 ≥ 3.11

### Helper script 沒執行權限
```bash
chmod +x ~/diet-coach/scripts/*.py
```

### `~/diet-coach/diet_log.csv: No such file or directory`
重做安裝步驟 3：把 `diet_log.csv`、`weight_log.csv`、`food_reference.csv`、`scripts/` 都複製到 `~/diet-coach/`。

### Bot 上線但訊息沒回應（ctb option B）
- `ctb` 啟動前要 `source .env`，否則 `TELEGRAM_BOT_TOKEN` 沒進環境變數
- 檢查 `.env` 裡的 `TELEGRAM_ALLOWED_USERS` 含你自己的 user_id（從 `@userinfobot` 取）
- BotFather 給的 token 拷貝完整（含開頭數字與冒號）

### `food-ref-append.py` 寫不進去
- 設 `DIET_COACH_FOOD_REF` 環境變數指向你的 CSV：`export DIET_COACH_FOOD_REF=~/diet-coach/food_reference.csv`
- 或建立 symlink：`ln -s ~/diet-coach/food_reference.csv ~/diet-coach/food_reference.csv`（預設路徑）

## 注意事項

- 誤差約 ±15–20%，外食尤其如此。這套不取代營養師，是個誠實的飲食日記
- 你的 `diet_log.csv` 與 `weight_log.csv` 是個人健康資料——放私有 repo 或 Google Drive，別 push 上來
- 公版只放模板與 helper scripts，沒人會看到你昨天吃什麼
- 想貢獻品牌包裝食品資料？來 [CONTRIBUTING.md](CONTRIBUTING.md)
