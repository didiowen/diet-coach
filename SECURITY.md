# Security Policy

## 回報弱點

發現安全性問題請**不要**開公開 issue，改用以下任一管道：

- GitHub 私密回報：repo 頁面 **Security → Report a vulnerability**
- 沒有 GitHub 帳號的話，聯絡 repo owner（profile 頁面）

回報請附上重現步驟與影響範圍，會盡快回覆（此為個人維護的專案，非商業 SLA）。

## 資料與隱私

本 repo 是**模板**，不含任何個人健康資料：

- `diet_log.csv`／`weight_log.csv` 只有欄位標頭；你的實際紀錄留在你自己的私有目錄，絕不要 push 回本 repo。
- `food_reference.csv` 是公開的食品營養標示資料（食藥署資料庫＋包裝標示），非個人紀錄。
- Helper scripts 全部離線運作，唯二例外：`familymart-lookup.py`（查全家食安 API）與 `backfill-food-ref-minerals.py`（查食藥署 open data），皆不上傳任何資料。

## 支援版本

只支援最新 release；舊版問題請先升級再回報。
