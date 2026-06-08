# diet-coach

透過 Telegram 傳送食物照片或文字，讓 Claude Code 自動估算熱量和巨量營養素，並記錄到本地 CSV 檔。

## 功能

- 辨識台灣常見料理（便當、自助餐、夜市、超商）
- 二段式每日目標：訓練日 / 休息日分開設定
- 從照片自動讀取營養標示 → 寫入 `food_reference.csv`
- 估算時考慮烹調方式（炒油、油炸等）影響
- 給範圍而非假精確值
- NG食物週計數：7天內超過設定次數自動嚴厲提醒

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
2. 修改 `SKILL.md` 中的使用者背景與營養目標
3. 建立個人資料目錄（例如 `~/diet-coach/` 或放在私有 repo 中）
4. 將 `diet_log.csv`、`food_reference.csv` 模板複製到該目錄
5. 透過 [claude-plugins-official](https://github.com/claude-plugins-official) 將 Claude Code 連接 Telegram
6. 傳送食物照片或描述，Claude 自動處理

## 個人化設定

在 `SKILL.md` 中調整以下區塊：

- **使用者背景**：體重、飲食偏好、所在地
- **營養目標**：訓練日 / 休息日的熱量、蛋白質、碳水、脂肪目標
- **NG食物管理**：定義哪些食物算 NG、每週限制次數、超標時的回應風格

## 注意事項

- 估算值誤差約 ±15–20%，外食尤其如此
- 此 repo 為公開模板，不含個人飲食記錄
- 個人資料（diet_log.csv 實際內容、food_reference.csv 填充值）建議放私有 repo
