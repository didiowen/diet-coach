#!/usr/bin/env python3
"""
openfoodfacts-lookup.py — 查詢 Open Food Facts API，取得商品營養素並寫入 food_reference.csv

流程：
  1. 條碼 → GET world.openfoodfacts.org/api/v2/product/{barcode}.json
     或關鍵字 → GET search.openfoodfacts.org/search（新版 search-a-licious API；
     舊版 cgi/search.pl 目前回傳 "Page temporarily unavailable"，改走新版）
  2. 優先採用 per-serving 欄位（*_serving，需 OFF 貢獻者填過才有）；
     否則退回 per-100g（於 notes 標明「無標準份量」，需自行換算實際攝取量）
  3. 熱量欄位若缺 energy-kcal，退回用 energy-kj 換算（÷4.184）
  4. 呼叫 food-ref-append.py 寫入 food_reference.csv（dedupe + flock 保護）

Open Food Facts 是全球開放資料庫，歐美/日韓進口食品覆蓋率較全家/食藥署完整，
但台灣本土品項少、資料由使用者自行填寫可能有誤——寫入前務必人工核對顯示的數值。

Usage:
  python3 openfoodfacts-lookup.py 3017620422003            # 條碼直查
  python3 openfoodfacts-lookup.py --search "oreo"           # 關鍵字搜尋
  python3 openfoodfacts-lookup.py 3017620422003 --list-only # 只顯示不寫入
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

PRODUCT_URL = "https://world.openfoodfacts.org/api/v2/product"
SEARCH_URL = "https://search.openfoodfacts.org/search"
FOOD_REF_APPEND = Path(__file__).parent / "food-ref-append.py"
FIELDS = "code,product_name,product_name_zh,product_name_en,brands,quantity,serving_size,nutriments"
USER_AGENT = "diet-coach-personal/1.0 (+https://github.com/didiowen/diet-coach)"


def api_get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def lookup_barcode(barcode: str) -> dict | None:
    """條碼直查，回傳 product dict 或 None"""
    url = f"{PRODUCT_URL}/{barcode}.json?fields={FIELDS}"
    data = api_get(url)
    if data.get("status") != 1:
        return None
    return data.get("product")


def search_products(keyword: str, page_size: int = 15) -> list[dict]:
    """關鍵字搜尋（search-a-licious API），回傳候選商品清單"""
    q = urllib.parse.urlencode({"q": keyword, "page_size": page_size, "fields": FIELDS})
    data = api_get(f"{SEARCH_URL}?{q}")
    return data.get("hits", []) or []


def parse_serving_g(serving_size: str) -> float | None:
    """從 OFF serving_size 字串解析公克數，例：'30 g'、'1 bar (40g)'"""
    if not serving_size:
        return None
    m = re.search(r"([\d.]+)\s*g\b", serving_size, re.IGNORECASE)
    return float(m.group(1)) if m else None


def to_kcal(n: dict, suffix: str) -> float | None:
    """suffix: '100g' 或 'serving'。優先用 kcal 欄位，缺的話從 kJ 換算（÷4.184）"""
    kcal = n.get(f"energy-kcal_{suffix}")
    if kcal is not None:
        return kcal
    kj = n.get(f"energy-kj_{suffix}")
    if kj is not None:
        return round(kj / 4.184, 1)
    return None


def extract_nutrition(product: dict) -> dict:
    """優先用 per-serving 欄位；否則退回 per-100g（附註標明）"""
    n = product.get("nutriments", {}) or {}
    serving_g = parse_serving_g(product.get("serving_size", "") or "")

    if serving_g:
        cal = to_kcal(n, "serving")
        protein = n.get("proteins_serving")
        carb = n.get("carbohydrates_serving")
        fat = n.get("fat_serving")
        if None not in (cal, protein, carb, fat):
            return {"serving_g": serving_g, "calories": cal, "protein": protein,
                     "carb": carb, "fat": fat, "per_100g": False}

    return {
        "serving_g": 100.0,
        "calories": to_kcal(n, "100g"),
        "protein": n.get("proteins_100g"),
        "carb": n.get("carbohydrates_100g"),
        "fat": n.get("fat_100g"),
        "per_100g": True,
    }


def product_name(product: dict) -> str:
    return (product.get("product_name_zh") or product.get("product_name")
            or product.get("product_name_en") or "").strip()


def normalize_brands(brands) -> str:
    if isinstance(brands, list):
        return "、".join(brands)
    return (brands or "").strip()


def append_to_food_ref(name: str, serving_g: float, calories: float,
                        protein: float, carb: float, fat: float, notes: str) -> bool:
    cmd = [
        sys.executable, str(FOOD_REF_APPEND),
        "--food-name", name,
        "--source", "Open Food Facts",
        "--serving-size-g", str(serving_g),
        "--calories", str(calories),
        "--protein-g", str(protein),
        "--carb-g", str(carb),
        "--fat-g", str(fat),
        "--notes", notes,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout.strip() or result.stderr.strip())
    return result.returncode == 0


def process_product(product: dict, list_only: bool = False) -> bool:
    name = product_name(product)
    if not name:
        print(f"  ⚠️  條碼 {product.get('code')} 查無品名")
        return False

    nut = extract_nutrition(product)
    brand = normalize_brands(product.get("brands"))
    quantity = product.get("quantity", "")

    print(f"\n商品：{name}" + (f"（{brand}）" if brand else ""))
    print(f"  份量：{nut['serving_g']}g" + ("（每100g估算，非實際包裝份量）" if nut["per_100g"] else ""))
    if quantity:
        print(f"  包裝標示：{quantity}")
    print(f"  熱量：{nut['calories']} kcal" if nut["calories"] is not None else "  熱量：（未提供）")
    print(f"  蛋白質：{nut['protein']}g  碳水：{nut['carb']}g  脂肪：{nut['fat']}g")

    if list_only:
        return True

    if any(v is None for v in (nut["calories"], nut["protein"], nut["carb"], nut["fat"])):
        print("  ⚠️  營養素不完整，跳過寫入")
        return False

    notes_parts = []
    if brand:
        notes_parts.append(brand)
    if quantity:
        notes_parts.append(f"包裝{quantity}")
    if nut["per_100g"]:
        notes_parts.append("每100g（OFF無標準份量資料，請自行換算實際攝取量）")
    notes_str = "；".join(notes_parts)

    return append_to_food_ref(name, nut["serving_g"], nut["calories"],
                               nut["protein"], nut["carb"], nut["fat"], notes_str)


def main():
    parser = argparse.ArgumentParser(description="Open Food Facts 查詢並寫入 food_reference.csv")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("barcode", nargs="?", help="條碼（EAN-13 等）")
    group.add_argument("--search", help="關鍵字搜尋")
    parser.add_argument("--list-only", action="store_true", help="只列出結果，不寫入 CSV")
    args = parser.parse_args()

    if args.barcode:
        try:
            product = lookup_barcode(args.barcode)
        except Exception as e:
            print(f"錯誤：{e}")
            sys.exit(1)
        if not product:
            print(f"查無條碼 {args.barcode}")
            sys.exit(0)
        process_product(product, list_only=args.list_only)
        return

    print(f"搜尋「{args.search}」...")
    try:
        results = search_products(args.search)
    except Exception as e:
        print(f"錯誤：{e}")
        sys.exit(1)

    if not results:
        print("找不到相符商品")
        sys.exit(0)

    print(f"找到 {len(results)} 項商品：\n")
    for i, p in enumerate(results, 1):
        name = product_name(p) or "(無品名)"
        brand = normalize_brands(p.get("brands"))
        print(f"  [{i:2d}] {name}" + (f"（{brand}）" if brand else "") + f"  code={p.get('code')}")

    if args.list_only:
        return

    print("\n請輸入要寫入的編號（逗號分隔，例：1,3；直接按 Enter 全部寫入；q 取消）：", end="")
    try:
        choice = input().strip()
    except (EOFError, KeyboardInterrupt):
        print("\n取消")
        return

    if choice.lower() == "q":
        print("取消")
        return

    if choice == "":
        selected = results
    else:
        try:
            indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected = [results[i] for i in indices if 0 <= i < len(results)]
        except (ValueError, IndexError):
            print("輸入有誤，取消")
            sys.exit(1)

    ok = 0
    for p in selected:
        if process_product(p):
            ok += 1

    print(f"\n完成：{ok}/{len(selected)} 筆寫入成功")


if __name__ == "__main__":
    main()
