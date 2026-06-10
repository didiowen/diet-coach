# 飲食教練

[![Made in Taiwan](https://img.shields.io/badge/Made%20in-Taiwan%20%F0%9F%87%B9%F0%9F%87%BC-red)](https://github.com/htlin222/society-calendar)
[![Codex CLI](https://img.shields.io/badge/Codex%20CLI-Telegram%20Bot-blue?logo=openai)](https://developers.openai.com/codex)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

透過 Telegram 傳送食物照片或文字，讓 Codex CLI 自動估算熱量和巨量營養素，並記錄到本地 CSV 檔。

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
2. Codex 讀取此 repo 的 `SKILL.md`，估算營養素（附誤差範圍），必要時主動詢問
3. 依 `SKILL.md` 規則回覆使用者，並在需要時更新本地 CSV 檔案

## 檔案說明

| 檔案 | 用途 |
|------|------|
| `SKILL.md` | Codex skill 設定——行為規則、目標、估算原則 |
| `diet_log.csv` | 模板：逐餐營養記錄 |
| `food_reference.csv` | 模板：食品資料庫（可從照片自動累積） |

## CSV 欄位

**diet_log.csv**
```
date, meal_type, food, calories, protein_g, carb_g, fat_g, training_day, notes
```

**food_reference.csv**
```
food_name, source, serving_size_g, calories, protein_g, carb_g, fat_g, notes
```

## Codex Telegram Bot

這個 repo 可以直接作為一個獨立的 Telegram bot 執行，後端由 Codex CLI 驅動，不需要把 Claude Code Telegram plugin 當成主要流程。

### 前置需求

- Node.js 22 以上
- 已安裝並完成認證的 Codex CLI，或準備 `CODEX_API_KEY`
- 由 `@BotFather` 建立的 Telegram bot token
- 要填入 `TELEGRAM_ALLOWED_USER_IDS` 的數字型 Telegram 使用者 ID

### 設定步驟

1. 安裝依賴：
   ```bash
   npm install
   ```
2. 以 `.env.example` 建立 `.env`
3. 填入必要的環境變數
4. 啟動開發模式：
   ```bash
   npm run dev
   ```

`npm start` 會依執行中的模組位置回推此 repo 根目錄，因此即使從其他 working directory 啟動 `node dist/src/index.js`，仍會使用這個 repo 的 `.env` 與工作目錄。

### `.env` 必填值

```dotenv
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USER_IDS=
```

### `.env` 選填值

```dotenv
# 若 Codex CLI 已完成登入，可留空
CODEX_API_KEY=
CODEX_MODEL=
CODEX_SANDBOX_MODE=workspace-write
CODEX_APPROVAL_POLICY=never
MAX_FILE_SIZE=20971520
```

### Bot 如何運作

- 使用者可在 Telegram 傳送餐點描述或食物照片
- Codex 會讀取此 repo 的 `SKILL.md`，依規則估算熱量與巨量營養素
- 當 `SKILL.md` 要求時，bot 會更新本地 CSV 檔案，例如 `diet_log.csv` 或 `food_reference.csv`

## 其他啟動方式

若你仍想沿用 Claude Code 搭配 Telegram plugin 的做法，可以自行另外配置；但這已不是本 repo 的主要支援路徑。

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

- **初始設定**：首次使用時 Codex 會詢問基本資料，自動計算 BMR/TDEE 並設定目標
- **NG食物管理**：定義哪些食物算 NG、每週限制次數、超標時的回應風格

## 注意事項

- 估算值誤差約 ±15–20%，外食尤其如此
- 此 repo 為公開模板，不含個人飲食記錄
- `diet_log.csv` 實際內容含個人健康資料，建議放私有 repo 或 Google Drive
- 歡迎共同維護`food_reference.csv`
