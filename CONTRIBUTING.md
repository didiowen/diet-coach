# 貢獻指南

感謝你願意協助維護 `food_reference.csv`！這份資料庫收錄台灣常見包裝食品的營養資訊，目標是建立一份可信賴的公共資料集。

## 接受哪些貢獻

**只接受以下來源的資料：**
- 食品包裝背面的正式營養標示
- 便利商店（7-11、全家、萊爾富、OK）官方標示或APP顯示值
- 連鎖品牌官網或產品頁面的標示值

**不接受：**
- 個人估算值（自煮料理、外食估算）
- 非台灣地區食品（暫不收錄，請另開 Issue 討論）
- 重複條目（提交前請搜尋 CSV 確認食品名稱不存在）

## 命名規範

食品名稱格式：`品牌 + 產品全名`，不縮寫。

| 正確 | 避免 |
|------|------|
| 義美生醫W PROTEIN抹茶乳清 | 義美抹茶乳清 |
| 光泉無加糖濃黑豆漿特濃5.1 | 光泉黑豆漿 |
| 全家FamilyMart日式和風沙拉醬 | 全家和風醬 |

## CSV 欄位說明

```
food_name, source, serving_size_g, calories, protein_g, carb_g, fat_g, notes
```

| 欄位 | 說明 | 範例 |
|------|------|------|
| `food_name` | 品牌 + 產品全名 | `光泉無加糖濃黑豆漿特濃5.1` |
| `source` | 品牌或通路 | `光泉`、`7-11`、`全家FamilyMart` |
| `serving_size_g` | 每份量（公克）；液體以 mL 直接換算 | `375` |
| `calories` | 熱量（kcal） | `204` |
| `protein_g` | 蛋白質（g） | `19.1` |
| `carb_g` | 碳水化合物（g） | `11.6` |
| `fat_g` | 脂肪（g） | `9.8` |
| `notes` | 口味、規格、備註 | `每盒375ml；黑豆；標示值` |

**`notes` 欄位必填「標示值」**，讓未來使用者知道這是官方數字。

## 提交流程

1. Fork 此 repo
2. 用 **`scripts/food-ref-append.py`** 加入新條目（**不要**手動編輯 CSV——see below）：
   ```bash
   DIET_COACH_FOOD_REF=./food_reference.csv \
     python3 scripts/food-ref-append.py \
       --food-name "光泉無加糖濃黑豆漿特濃5.1" --source "光泉" \
       --serving-size-g 375 --calories 204 \
       --protein-g 19.1 --carb-g 11.6 --fat-g 9.8 \
       --notes "每盒375ml；黑豆；標示值"
   ```
   - 腳本內含 `fcntl.flock` 序列化 + `(food_name, source)` dedupe，race-safe
   - 重複品項自動 skip（同名同來源），所以 idempotent；可放心多次執行
   - 透過 helper 寫入比手動編輯 CSV 安全：保證欄位順序、escape、編碼正確
3. 開 Pull Request，填寫 PR template
4. 維護者審查後合併

### 為何不能手動編輯 CSV？

- 多人同時提交時，手動編輯 + 直接 commit 容易吃掉別人的條目
- 中文逗號、引號、跨行 notes 容易破壞 CSV 解析
- `food-ref-append.py` 用 Python `csv.DictWriter`，escape 規則正確

如果你的環境跑不動 Python（罕見），請在 PR 描述貼出新條目的 CSV 文字，維護者會幫你執行 helper 寫入。

## 常見問題

**Q: 同一食品有多種口味，要分開提交嗎？**
A: 是的，每種口味各一行（營養成分不同）。

**Q: 我找不到某品牌的官方資料怎麼辦？**
A: 開 Issue 說明，讓社群協助找資料；不要提交估算值。

**Q: 食品已下架或換代，要更新嗎？**
A: 開 Issue 說明，維護者會標記或移除。
