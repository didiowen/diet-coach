# 飲食教練

[![Made in Taiwan](https://img.shields.io/badge/Made%20in-Taiwan%20%F0%9F%87%B9%F0%9F%87%BC-red)](https://github.com/htlin222/society-calendar)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill%20Based-blueviolet?logo=anthropic)](https://claude.ai/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

透過 Telegram 傳送食物照片或文字，讓 Claude Code 或 Codex 自動估算熱量和巨量營養素，並記錄到本地 CSV 檔。

## 功能

- 辨識台灣常見料理（便當、自助餐、夜市、超商）
- 二段式每日目標：訓練日 / 休息日分開設定
- 從照片自動讀取營養標示 → 寫入 `food_reference.csv`
- 估算時考慮烹調方式（炒油、油炸等）影響
- 給範圍而非假精確值
- NG食物週計數：7天內超過設定次數自動嚴厲提醒
- 體重追蹤：每2週自動提醒量體重，回報後以 Mifflin-St Jeor 重算 BMR/TDEE，確認後更新目標

## 運作方式

1. 透過 Telegram bot 傳送食物照片或文字描述
2. Claude 或 Codex 讀取 `SKILL.md`，估算營養素（附誤差範圍），必要時主動詢問
3. 結果 append 到 `diet_log.csv`，並 git commit / push

## 檔案說明

| 檔案 | 用途 |
|------|------|
| `SKILL.md` | Claude Code / Codex skill 設定——行為規則、目標、估算原則 |
| `diet_log.csv` | 模板：逐餐營養記錄 |
| `food_reference.csv` | 模板：食品資料庫（可從照片自動累積） |
| `weight_log.csv` | 模板：體重/體脂歷史記錄 |

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

1. 將 `SKILL.md` 放到 `~/.claude/skills/diet-coach/SKILL.md`
2. 建立個人資料目錄（例如私有 git repo）
3. 將 `diet_log.csv`、`food_reference.csv` 模板複製到該目錄，並在 `SKILL.md` 更新路徑
4. 設定 Telegram（見下方教學）
5. 傳送食物照片或描述，Claude 自動處理

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
cd ~/diet-coach && ctb
```

Bot 上線後 DM 它即可。ctb 把訊息路由到啟動時的工作目錄，並自動把相片下載成本地檔案路徑供 Claude 或 Codex 讀取；無需另外設定相片處理。

**（選用）改用 Codex / ChatGPT 免費額度**

ctb 內建 `claude` 與 `codex` 兩個 provider。如果想省 Claude token，可改走 ChatGPT 帳號的免費 Codex 額度：

1. 先在 terminal 跑一次 `codex` CLI 完成 OAuth（產出 `~/.codex/auth.json`）— 詳見 [openai/codex](https://github.com/openai/codex)
2. ctb 啟動後 DM bot 打 `/provider codex` 切換

注意：diet-coach 的 prompt 都在 Claude 上調校，Codex（GPT-5.x）的食物估算與 zh-TW 輸出品質請自行實測。

ctb 進階用法（多人 allowlist 各自 routing、`/cd` 切換工作目錄、相片下載等）詳見 [htlin222/claude-telegram-bot](https://github.com/htlin222/claude-telegram-bot) README。

## BMR / TDEE 計算方式

`SKILL.md` 在初始設定時會詢問使用者資料，並以 **Mifflin-St Jeor（1990）** 公式計算基礎代謝率（BMR）：

| 性別 | 公式 |
|------|------|
| 男 | BMR = 10 × 體重(kg) + 6.25 × 身高(cm) − 5 × 年齡 + 5 |
| 女 | BMR = 10 × 體重(kg) + 6.25 × 身高(cm) − 5 × 年齡 − 161 |

再乘上活動係數（PAL）得出 **TDEE（每日總熱量消耗）**：

| 活動量 | PAL |
|--------|-----|
| 幾乎不動 | 1.20 |
| 輕度活動（1–3次/週） | 1.375 |
| 中度活動（3–5次/週） | 1.55 |
| 重度活動（6–7次/週） | 1.725 |
| 極重度活動 | 1.90 |

依目標調整熱量：減脂 TDEE × 0.80–0.85、增肌 TDEE × 1.05–1.10、維持 TDEE。

> 可用 [王介立醫師臨床計算器](https://copper0722.com.tw/calculator/topic/body-size-energy/) 驗算。

## 個人化設定

在 `SKILL.md` 中調整以下區塊：

- **初始設定**：首次使用時 Claude 或 Codex 會詢問基本資料，自動計算 BMR/TDEE 並設定目標
- **NG食物管理**：定義哪些食物算 NG、每週限制次數、超標時的回應風格

## 注意事項

- 估算值誤差約 ±15–20%，外食尤其如此
- 此 repo 為公開模板，不含個人飲食記錄
- `diet_log.csv`、`weight_log.csv` 實際內容含個人健康資料，建議放私有 repo 或 Google Drive
- 歡迎共同維護`food_reference.csv`
