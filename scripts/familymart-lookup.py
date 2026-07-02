#!/usr/bin/env python3
"""
familymart-lookup.py — 查詢全家食安網 API，取得商品完整營養素並寫入 food_reference.csv

流程：
  1. 關鍵字 → QueryFsProductListByFilter → 取得 CMNO + 商品名稱清單
  2. CMNO → QueryFsProductByItem → 取得 NUTRIENTS（P/C/F + 熱量）
  3. 解析 NOTE 取得每份公克數
  4. 呼叫 food-ref-append.py 寫入 food_reference.csv（dedupe + flock 保護）

Usage:
  python3 familymart-lookup.py "嫩烤雞胸"
  python3 familymart-lookup.py --cmno 0357416
  python3 familymart-lookup.py "雞胸" --list-only   # 只列出搜尋結果，不寫入
"""

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE_URL = "https://foodsafety.family.com.tw/Web_FFD_2022/ws/"
FOOD_REF_APPEND = Path(__file__).parent / "food-ref-append.py"


def api_post(endpoint: str, payload: dict) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + endpoint,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def search_products(keyword: str) -> list[dict]:
    """關鍵字搜尋，回傳 [{cmno, name, note, category}] 清單"""
    data = api_post("QueryFsProductListByFilter", {"MEMBER": "N", "KEYWORD": keyword})
    if data.get("RESULT_CODE") != "00":
        raise RuntimeError(f"搜尋失敗: {data.get('RESULT_DESC')}")
    results = []
    for cat in data.get("LIST", []):
        cat_name = cat.get("CATEGORY_NAME", "")
        for item in cat.get("ITEM", []):
            results.append({
                "cmno": item["CMNO"],
                "name": item["PRODNAME"],
                "note": item.get("NOTE", ""),
                "category": cat_name,
            })
    return results


def get_product_detail(cmno: str) -> dict | None:
    """用 CMNO 查詳細營養素，回傳 dict 或 None"""
    data = api_post("QueryFsProductByItem", {"MEMBER": "N", "CMNO": cmno})
    if data.get("RESULT_CODE") != "00":
        return None
    lst = data.get("LIST", [])
    if not lst:
        return None
    return lst[0]


def parse_serving_g(note: str) -> float | None:
    """從 NOTE 字串解析每份公克數，例：'每份規格120公克' → 120.0"""
    m = re.search(r"每份規格\s*([\d.]+)\s*公克", note)
    if m:
        return float(m.group(1))
    # 備案：直接找數字+公克
    m = re.search(r"([\d.]+)\s*公克", note)
    if m:
        return float(m.group(1))
    return None


def parse_calories_from_note(note: str) -> float | None:
    """從 NOTE 解析熱量，例：'每份熱量148.8大卡' → 148.8"""
    m = re.search(r"每份熱量\s*([\d.]+)\s*大卡", note)
    if m:
        return float(m.group(1))
    return None


def append_to_food_ref(name: str, serving_g: float, calories: float,
                        protein: float, carb: float, fat: float, notes: str) -> bool:
    cmd = [
        sys.executable, str(FOOD_REF_APPEND),
        "--food-name", name,
        "--source", "全家FamilyMart",
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


def process_item(cmno: str, search_note: str = "", list_only: bool = False) -> bool:
    detail = get_product_detail(cmno)
    if not detail:
        print(f"  ⚠️  CMNO {cmno} 無法取得詳細資料")
        return False

    name = detail.get("PRODNAME", "")
    note = detail.get("NOTE", "") or search_note
    nutrients = detail.get("NUTRIENTS", [{}])[0] if detail.get("NUTRIENTS") else {}

    protein = nutrients.get("PROTEIN")
    fat = nutrients.get("TOTALFAT")
    carb = nutrients.get("CARBOHYDRATE")
    sodium = nutrients.get("SODIUM")

    serving_g = parse_serving_g(note)
    calories = parse_calories_from_note(note)

    # 若無法解析份量，設為 100g（常見預設）
    if serving_g is None:
        serving_g = 100.0

    print(f"\n商品：{name}")
    print(f"  份量：{serving_g}g")
    print(f"  熱量：{calories} kcal" if calories else "  熱量：（未解析）")
    print(f"  蛋白質：{protein}g  碳水：{carb}g  脂肪：{fat}g")
    if sodium is not None:
        print(f"  鈉：{sodium}mg")

    if list_only:
        return True

    if protein is None or fat is None or carb is None or calories is None:
        print("  ⚠️  營養素不完整，跳過寫入")
        return False

    notes_str = f"{note.strip().rstrip(';')}；鈉{sodium}mg" if sodium else note.strip().rstrip(";")

    return append_to_food_ref(name, serving_g, calories, protein, carb, fat, notes_str)


def main():
    parser = argparse.ArgumentParser(description="全家食安 API 查詢並寫入 food_reference.csv")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("keyword", nargs="?", help="搜尋關鍵字")
    group.add_argument("--cmno", help="直接指定商品 CMNO")
    parser.add_argument("--list-only", action="store_true", help="只列出結果，不寫入 CSV")
    args = parser.parse_args()

    if args.cmno:
        process_item(args.cmno, list_only=args.list_only)
        return

    # 關鍵字搜尋
    print(f"搜尋「{args.keyword}」...")
    try:
        results = search_products(args.keyword)
    except RuntimeError as e:
        print(f"錯誤：{e}")
        sys.exit(1)

    if not results:
        print("找不到相符商品")
        sys.exit(0)

    print(f"找到 {len(results)} 項商品：\n")
    for i, item in enumerate(results, 1):
        print(f"  [{i:2d}] {item['name']}  ({item['category']})  CMNO={item['cmno']}")
        if item["note"]:
            print(f"       {item['note']}")

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
    for item in selected:
        if process_item(item["cmno"], item["note"]):
            ok += 1

    print(f"\n完成：{ok}/{len(selected)} 筆寫入成功")


if __name__ == "__main__":
    main()
