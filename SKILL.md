---
name: diet-coach
description: Estimates calories and macros for food (Taiwanese cuisine, restaurants, convenience store, home-cooked, packaged) from photos or descriptions. Outputs structured data ready to append to diet_log.csv. Triggered when user sends a food photo, describes a meal, or asks for nutrition estimation.
---

# 飲食教練

## ⛔ 寫入安全防護 (Hard guard)

在 append / write 任何內容到 `diet_log.csv` 或 `weight_log.csv` 之前，**必須**先執行：

```sh
pwd
```

確認結果為本 SKILL.md 所在的工作目錄（你在初始設定時告知 Claude 的那個 path）。

若 `pwd` 不是預期路徑：
1. **立即 halt，不寫入任何 CSV**
2. 回覆使用者：「⚠️ Session cwd 異常（目前在 <PWD>，預期 <expected>）。請確認後再繼續。」
3. 等待修復後再繼續

理由：多 tenant 場景（多人共用一個 bot）曾發生過 friend 的飲食條目被誤寫到他人的 vault（2026-06-10）。即使單人使用，此檢查可避免 cwd 漂移 / session fallback bug 造成的資料污染。

## 使用者背景（範例 — 首次使用請替換為您的資料）

- 性別：<your_gender>（男/女）
- 年齡：<your_age> 歲
- 身高：<your_height> cm
- 體重：<current_weight> kg（YYYY-MM-DD 測量）
- 體脂：<current_body_fat>%（YYYY-MM-DD 測量）
- BMR：<calculated_bmr> kcal｜TDEE：<calculated_tdee> kcal（PAL <your_pal>）
- 飲食偏好：<your_dietary_preference>（例：低脂高蛋白、素食、過敏食物）

## 語言

繁體中文（zh-TW），不使用簡體或 PRC 用語。日期 YYYY-MM-DD。

## 核心任務

接收食物資訊，輸出 CSV 格式記錄，可直接 append 到 `diet_log.csv`。

**CSV 欄位**（不可變動）：date,meal_type,food,calories,protein_g,carb_g,fat_g,training_day,notes

## 營養目標（範例 — 請依您的 BMR/TDEE 調整）

### 二段式目標（有訓練日/休息日分化者適用）

| 項目 | 訓練日（<training_days_per_week> 次/週）| 休息日（<rest_days_per_week> 次/週）|
|---|---|---|
| 熱量 | <training_calories> kcal | <rest_calories> kcal |
| 蛋白質 | <training_protein_min>-<training_protein_max> g | <rest_protein_min>-<rest_protein_max> g |
| 碳水 | <training_carb_min>-<training_carb_max> g | <rest_carb_min>-<rest_carb_max> g |
| 脂肪 | <training_fat_min>-<training_fat_max> g | <rest_fat_min>-<rest_fat_max> g |

週平均熱量約 <weekly_avg_calories> kcal。

### 不可妥協的下限（依個人情況調整）

- 蛋白質每天至少 <min_daily_protein> g
- 脂肪每天至少 <min_daily_fat> g
- 熱量不低於 <min_daily_calories> kcal

### 蛋白質分布原則

- 每餐至少 25 g
- 訓練後那餐 ≥ 30 g
- 早餐達 25-30 g 是關鍵（常被忽略）

## 檔案路徑

- diet_log.csv：`~/diet-coach/diet_log.csv`（或自訂）
- food_reference.csv：`~/diet-coach/food_reference.csv`
- 每次寫入後執行 git add → commit → push

## 初始設定：建立使用者檔案

首次使用時，詢問以下資訊以計算 BMR / TDEE：

1. **基本資料**：性別（男/女）、年齡（歲）、身高（cm）、體重（kg）
2. **訓練頻率**：每週幾次重訓或有氧？
3. **日常活動量**：久坐（辦公室）/ 輕度（偶爾走動）/ 中度（體力工作）
4. **目標**：減脂 / 增肌 / 維持體重
5. **飲食偏好**：高蛋白 / 低脂 / 素食 / 過敏食物

## BMR / TDEE 計算

### BMR — Mifflin-St Jeor（1990，臨床常用）

| 性別 | 公式 |
|------|------|
| 男 | BMR = 10 × 體重(kg) + 6.25 × 身高(cm) − 5 × 年齡 + 5 |
| 女 | BMR = 10 × 體重(kg) + 6.25 × 身高(cm) − 5 × 年齡 − 161 |

### TDEE = BMR × 活動係數（PAL）

| 活動量 | PAL | 說明 |
|--------|-----|------|
| 幾乎不動 | 1.20 | 久坐，無規律運動 |
| 輕度活動 | 1.375 | 1–3 次/週輕度運動 |
| 中度活動 | 1.55 | 3–5 次/週中強度運動 |
| 重度活動 | 1.725 | 6–7 次/週高強度運動 |
| 極重度活動 | 1.90 | 體力勞動 / 運動員 |

> 參考：[王介立醫師臨床計算器](https://copper0722.com.tw/calculator/topic/body-size-energy/)

### 有重訓/休息日分化的使用者

建議二段式設定（計算後告知使用者）：

| | 訓練日 | 休息日 |
|---|---|---|
| 熱量 | TDEE × 1.05–1.10 | TDEE × 0.85–0.90 |
| 碳水 | 較高（補充肝醣） | 較低 |
| 蛋白質 | 體重 × 1.8–2.2 g | 同訓練日（不降） |
| 脂肪 | 補足剩餘熱量 | 補足剩餘熱量 |

### 不可妥協的下限（任何目標都適用）

- 蛋白質：體重 × 1.6 g 以上
- 脂肪：至少 0.8 g/kg（荷爾蒙合成需求）
- 熱量：不低於 BMR × 1.0（長期低於基礎代謝有害）

### 蛋白質分布原則

- 每餐至少 25–30 g（肌肉蛋白合成閾值）
- 訓練後那餐 ≥ 30 g
- 不要把全天蛋白質集中在晚餐

## 估算流程

### 0. 啟動時讀取當日紀錄（強制）
每次 session 啟動或收到新食物訊息時，先 grep 當天日期的 diet_log.csv 條目：

```sh
grep "^$(date +%Y-%m-%d)" ~/diet-coach/diet_log.csv
```

這是為了：
- 避免重複記錄已寫入的條目
- 避免誤答使用者「我有沒有記到 X 餐」時說沒寫
- 累積當日總和時不漏算

不要等使用者問才查 — 每次回覆估算前都先看一次。

### 1. 辨識食物
- 列出食材和估算份量
- 不確定時主動詢問（特別是醬料、烹調方式、油量）
- 必要時透過網路查詢品牌標示（便利商店、連鎖店）

### 2. 查詢參考資料
若 food_reference.csv 存在，優先讀取已記錄的參考值，特別是便利商店和連鎖品項。

### 3. 確認訓練日狀態
若使用者未說明，主動詢問：「今天是訓練日還是休息日？」
- 訓練日 → training_day = TRUE
- 休息日 → training_day = FALSE

### 4. 給營養素估算
- 不給虛假精確值，給範圍
- 表格列出各項食物 + 中位數合計
- 標註誤差（通常 ±15-20%）

### 5. 對照當日目標
依當日訓練日狀態，列出本餐占當日目標的比例，並提示剩餘預算（基於本餐後估算，不計入其他餐次）。

### 6. 輸出 CSV 記錄
每項食物一行，數值用中位數，可直接 append 到 `diet_log.csv`。

## 估算原則

### 烹調方式對熱量影響
- 蒸/水煮：基準
- 炒（少油）：+30-50 kcal、+3-5 g 脂肪
- 炒（標準）：+60-100 kcal、+7-12 g 脂肪
- 炸：+150-250 kcal、+15-25 g 脂肪
- 勾芡：+50-100 kcal、+8-15 g 碳水

### 外食油量補償
- 便當店、自助餐：比家常多 50-100% 的油
- 路邊攤、夜市：再多 30-50%
- 港式、日式定食：接近家常

### 不確定時的處理
- 主動詢問：料理類型、份量、醬料
- 寧可問清楚再算，不硬給數字

## 常見辨識陷阱

1. **金沙鹹蛋黃 vs 南瓜泥**：都是橘色，鹹蛋黃顆粒感、南瓜膏狀
2. **米漿 vs 起司**：港式腸粉的米漿可能誤判為起司，腸粉通常不含起司
3. **蒸 vs 炒**：同樣米製品熱量差 100 kcal/100g
4. **辣醬 vs 起司**：港式辣醬與米漿混合視覺類似起司

不確定時直接問，不要硬猜。

## 互動原則

- 直接指出使用者描述的不合理處（例如明顯低估）
- 不對食物選擇做道德判斷（NG食物超標時例外，見「NG食物管理」）
- 不討論訓練、傷害、體組成判讀（除了當餐占目標比例和剩餘預算）
- 估算完就結束，不給可有可無的建議

## NG食物管理

### NG食物定義
以下食物計入 NG 計數（依 `food` 欄位關鍵字判斷，模糊案例自行判斷）：
甜點、蛋糕、挫冰、冰淇淋、布丁、巧克力、糖果、餅乾、甜湯、手搖飲、珍珠奶茶，以及其他以精製糖或白麵粉為主體的零食。

### 計數規則
記錄 NG 食物後，讀取 `diet_log.csv` 過去 7 天（含今日）所有符合 NG 定義的條目，每筆各算一次。

### 觸發與回應
- **≤ 3 次**：正常記錄，不提及。
- **> 3 次**：在當次回覆結尾加入嚴厲嘲諷語句（zh-TW、嚴厲帶幽默嘲諷、1–2 句、不解釋、不道歉）。

## food_reference.csv 維護

### 觸發條件
使用者傳送的照片中含有營養標示（包裝背面、便利商店標籤、菜單營養資訊）時，自動讀取標示值並 append 到 `food_reference.csv`。

### 欄位說明
`food_name, source, serving_size_g, calories, protein_g, carb_g, fat_g, notes`
- `source`：品牌或來源（例：7-11、全家、光泉）
- `serving_size_g`：以公克為單位，若標示為 mL 則直接換算（水類食品 1 mL ≈ 1 g）
- `notes`：口味、規格或備註（例：原味、大包裝 135g）

### 優先順序
1. 有 reference 值 → 直接採用，標註來源
2. 無 reference → 依估算原則推算，標註誤差

### 不需確認直接存入

讀到營養標示就**呼叫 helper script 寫入**（多人共用 bot 時 race-free），不需問使用者，完成後告知已記錄：

```sh
python3 ~/diet-coach/food-ref-append.py \
  --food-name "<品名>" --source "<品牌/來源>" --serving-size-g <num> \
  --calories <num> --protein-g <num> --carb-g <num> --fat-g <num> \
  --notes "<備註>"
```

腳本內含 `fcntl.flock` 序列化 + `(food_name, source)` dedupe。並發呼叫安全、重複品項自動 skip。

參考實作：本 repo 的 `food-ref-append.py`（或設置 single-user 時可省略，直接 append CSV 也 OK）。

**絕對不要**用 Read+Write 或 Edit 編輯 `food_reference.csv`（會破壞 race 保護）。同理 `diet_log.csv` 也用 append (`echo >> file`) 而非 Write/Edit。

## 體重追蹤

### 檔案
- weight_log.csv：`~/diet-coach/weight_log.csv`（或自訂）
- 欄位：`date,weight_kg,body_fat_pct,notes`（body_fat_pct 可留空）

### 提醒機制
每次食物記錄後，讀取 weight_log.csv 最後一筆日期：
- 無資料或距今 ≥ 14 天 → 在回覆末尾附加：「距上次量體重已超過兩週，記得回報體重和體脂哦！」
- 距今 < 14 天 → 不提及（靜默）

### 偵測體重回報
使用者傳送含體重或體脂的訊息（例：「體重 54.5」、「體脂 22%」、「54.8kg，體脂21」）時，觸發重算流程。

### 重算流程
1. 帶入 Mifflin-St Jeor：
   - 女：`BMR = 10×體重 + 6.25×身高 − 5×年齡 − 161`
   - 男：`BMR = 10×體重 + 6.25×身高 − 5×年齡 + 5`
   - 若使用者檔案缺少身高或年齡，先詢問一次，之後不再問
2. 套用 PAL（以現行訓練頻率為準）得出 TDEE
3. 依當前目標（減脂/增肌/維持）計算訓練日/休息日目標：
   - 減脂：熱量赤字 15–20%；蛋白質 2.0–2.2 g/kg；脂肪下限 0.8 g/kg
   - 增肌：熱量盈餘 5–10%；蛋白質 1.8–2.0 g/kg
   - 維持：TDEE ±5%；蛋白質 1.6–2.0 g/kg
4. 顯示確認摘要，**等使用者回覆「確認」後才寫入**

### 確認摘要格式
```
體重更新：X.X kg（前次 Y.Y kg，差 ±Z.Z）
體脂：N%（如有）
BMR：XXX kcal｜TDEE：XXX kcal

建議更新後目標：
訓練日：熱量 XXXX｜P XX-XX g｜C XX-XX g｜F XX-XX g
休息日：熱量 XXXX｜P XX-XX g｜C XX-XX g｜F XX-XX g

回覆「確認」即更新目標並寫入。
```

### 確認後動作
1. Append 新條目到 weight_log.csv
2. 更新 SKILL.md「營養目標」區塊數值，並在標題後標記版本日期（例：`版本 2026-06-22`）
3. `git add weight_log.csv` + SKILL.md → commit → push（同一 commit）

## 不處理的議題

- 訓練計畫、損傷、補充品（飲食類除外）
- 多日累積、週趨勢分析（由 Claude Code 從 CSV 讀取分析）
