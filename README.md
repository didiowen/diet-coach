# 飲食教練

[![Made in Taiwan](https://img.shields.io/badge/Made%20in-Taiwan%20%F0%9F%87%B9%F0%9F%87%BC-red)](https://github.com/htlin222/society-calendar)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill%20Based-blueviolet?logo=anthropic)](https://claude.ai/claude-code)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

透過 Telegram 傳送食物照片或文字，讓 Claude Code 自動估算熱量和巨量營養素，並記錄到本地 CSV 檔。

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
2. Claude 讀取 `SKILL.md`，估算營養素（附誤差範圍），必要時主動詢問
3. 結果 append 到 `diet_log.csv`，並 git commit / push

## 檔案說明

| 檔案 | 用途 |
|------|------|
| `SKILL.md` | Claude Code skill 設定——行為規則、目標、估算原則 |
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

> 完整教學：[Claude Code Telegram 快速設置](https://abmedia.io/claude-code-telegram-quick-setup)

### 前置需求

- 已安裝 Claude Code（`claude` 指令可執行）
- 已安裝 [Bun](https://bun.sh)：`curl -fsSL https://bun.sh/install | bash`

### 設置步驟

**Step 1 — 建立 Telegram Bot**

在 Telegram 搜尋 `@BotFather`，輸入 `/newbot`，依提示建立 Bot 並取得 Token（格式：`123456789:AAHfiqks...`）。

**Step 2 — 安裝插件**

進入 Claude Code session，執行：
```
/plugin install telegram@claude-plugins-official
/reload-plugins
```

**Step 3 — 設定 Token**

```
/telegram:configure 你的_BOT_TOKEN
```

**Step 4 — 以 Channels 模式重啟**

```bash
claude --channels plugin:telegram@claude-plugins-official
```

> 注意：必須加 `--channels` 參數，Bot 才會上線；單獨執行 `claude` 不會收到訊息。

**Step 5 — 配對**

1. 在 Telegram 傳任意訊息給 Bot → 收到 6 字元配對碼
2. 回到 Claude Code session，執行：`/telegram:access pair <配對碼>`
3. 確認提示選 **Yes**

**Step 6 — 鎖定存取**

```
/telegram:access policy allowlist
```

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

- **初始設定**：首次使用時 Claude 會詢問基本資料，自動計算 BMR/TDEE 並設定目標
- **NG食物管理**：定義哪些食物算 NG、每週限制次數、超標時的回應風格

## 注意事項

- 估算值誤差約 ±15–20%，外食尤其如此
- 此 repo 為公開模板，不含個人飲食記錄
- `diet_log.csv` 實際內容建議放私有 repo 或 google drive
- 歡迎共同維護`food_reference.csv`
