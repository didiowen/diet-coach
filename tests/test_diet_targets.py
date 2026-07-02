"""Tests for scripts/diet-targets.py."""
import json

from conftest import run_script

WEIGHT_LOG_HEADER = "date,height_cm,weight_kg,body_fat_pct,bmr,tdee,pal,notes"


def write_weight_log(path, rows, encoding="utf-8"):
    path.write_text(
        WEIGHT_LOG_HEADER + "\n" + "\n".join(rows) + ("\n" if rows else ""),
        encoding=encoding,
    )


def test_two_tier_cut_default(tmp_path):
    """Default goal=cut, tiers=2: train TDEE*0.90, rest TDEE*0.80."""
    write_weight_log(tmp_path / "weight_log.csv", ["2026-06-01,170,60,25,1400,2000,1.43,"])
    r = run_script("diet-targets.py", "--dir", str(tmp_path))
    assert r.returncode == 0
    assert "goal=cut" in r.stdout
    assert "訓練日：熱量 1800" in r.stdout
    assert "休息日：熱量 1600" in r.stdout
    assert "P 120-132 g" in r.stdout  # 60kg * 2.0-2.2
    assert "F 48-60 g" in r.stdout  # 60kg * 0.8-1.0


def test_three_tier_recomp_mid_is_midpoint(tmp_path):
    """--tiers 3 recomp: high 1.10, mid (1.10+0.90)/2 = 1.00, rest 0.90."""
    write_weight_log(tmp_path / "weight_log.csv", ["2026-06-01,170,60,25,1400,2000,1.43,"])
    r = run_script("diet-targets.py", "--dir", str(tmp_path), "--goal", "recomp", "--tiers", "3")
    assert r.returncode == 0
    assert "高強度日：熱量 2200" in r.stdout
    assert "中強度日：熱量 2000" in r.stdout
    assert "休息日：熱量 1800" in r.stdout


def test_goal_and_tiers_from_members_json(tmp_path):
    """Group mode reads goal/tiers from members.json by slug."""
    (tmp_path / "members.json").write_text(json.dumps(
        {"111": {"slug": "alex", "goal": "recomp", "tiers": 3}}
    ))
    write_weight_log(tmp_path / "weight_log_alex.csv", ["2026-06-01,170,60,25,1400,2000,1.43,"])
    r = run_script("diet-targets.py", "--dir", str(tmp_path), "--slug", "alex")
    assert r.returncode == 0
    assert "goal=recomp" in r.stdout
    assert "tiers=3" in r.stdout
    assert "中強度日：熱量 2000" in r.stdout


def test_invalid_goal_from_members_json_friendly_error(tmp_path):
    """A typo'd goal in members.json must not crash with a raw KeyError."""
    (tmp_path / "members.json").write_text(json.dumps(
        {"111": {"slug": "alex", "goal": "gain"}}
    ))
    write_weight_log(tmp_path / "weight_log_alex.csv", ["2026-06-01,170,60,25,1400,2000,1.43,"])
    r = run_script("diet-targets.py", "--dir", str(tmp_path), "--slug", "alex")
    assert r.returncode != 0
    assert "unknown goal 'gain'" in r.stderr
    assert "Traceback" not in r.stderr


def test_kcal_never_below_bmr(tmp_path):
    """Hard floor: sedentary cut rest-day (TDEE*0.80 < BMR) is lifted to BMR."""
    # PAL 1.20: TDEE 1680, BMR 1400 -> rest day would be 1344 < 1400
    write_weight_log(tmp_path / "weight_log.csv", ["2026-06-01,170,60,25,1400,1680,1.20,"])
    r = run_script("diet-targets.py", "--dir", str(tmp_path), "--goal", "cut")
    assert r.returncode == 0
    assert "休息日：熱量 1400（已提升至 BMR 下限）" in r.stdout
    assert "訓練日：熱量 1512" in r.stdout  # 1680*0.90, above floor, untouched


def test_malformed_trailing_row_falls_back(tmp_path):
    """One garbled last row must not discard an otherwise valid log."""
    write_weight_log(tmp_path / "weight_log.csv", [
        "2026-06-01,170,60,25,1400,2000,1.43,",
        "2026-06-02,170,,,,,,",
    ])
    r = run_script("diet-targets.py", "--dir", str(tmp_path))
    assert r.returncode == 0
    assert "TDEE=2000" in r.stdout


def test_bom_weight_log_parses(tmp_path):
    """Excel-saved (BOM) weight log must still be readable."""
    write_weight_log(tmp_path / "weight_log.csv",
                     ["2026-06-01,170,60,25,1400,2000,1.43,"], encoding="utf-8-sig")
    r = run_script("diet-targets.py", "--dir", str(tmp_path))
    assert r.returncode == 0
    assert "TDEE=2000" in r.stdout


def test_missing_weight_log_errors(tmp_path):
    r = run_script("diet-targets.py", "--dir", str(tmp_path))
    assert r.returncode != 0
    assert "no usable weight_log row" in r.stderr
