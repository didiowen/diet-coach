"""Tests for scripts/weight-log-append.py."""
import csv
import json

from conftest import run_script, write_diet_log


def read_rows(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def test_katch_mcardle_with_body_fat(tmp_path):
    """Body fat given -> Katch-McArdle, no profile needed; no diet log -> PAL 1.375."""
    r = run_script("weight-log-append.py", "--dir", str(tmp_path),
                   "--weight", "58.2", "--body-fat-pct", "24", "--date", "2026-06-14")
    assert r.returncode == 0, r.stderr
    rows = read_rows(tmp_path / "weight_log.csv")
    assert len(rows) == 1
    # LBM 58.2*0.76 = 44.232 -> BMR round(370 + 21.6*44.232) = 1325
    assert rows[0]["bmr"] == "1325"
    assert rows[0]["pal"] == "1.375"
    assert rows[0]["tdee"] == str(round(1325 * 1.375))


def test_mifflin_single_user_flags(tmp_path):
    """No body fat -> Mifflin-St Jeor from flags (male 70kg/178cm/30y)."""
    r = run_script("weight-log-append.py", "--dir", str(tmp_path),
                   "--weight", "70", "--height-cm", "178", "--age", "30",
                   "--gender", "male", "--date", "2026-06-14")
    assert r.returncode == 0, r.stderr
    rows = read_rows(tmp_path / "weight_log.csv")
    # 10*70 + 6.25*178 - 5*30 + 5 = 1667.5 -> 1668
    assert rows[0]["bmr"] == "1668"


def test_group_profile_from_members_json(tmp_path):
    """--slug pulls height/age/gender from members.json and writes weight_log_<slug>.csv."""
    (tmp_path / "members.json").write_text(json.dumps(
        {"111": {"slug": "alex", "height_cm": 178, "age": 30, "gender": "male"}}
    ))
    r = run_script("weight-log-append.py", "--dir", str(tmp_path),
                   "--slug", "alex", "--weight", "70", "--date", "2026-06-14")
    assert r.returncode == 0, r.stderr
    rows = read_rows(tmp_path / "weight_log_alex.csv")
    assert rows[0]["bmr"] == "1668"


def test_pal_counts_true_and_mid_days(tmp_path):
    """TRUE and MID training days both count toward PAL; 6/14 days -> 3.0/wk -> 1.55."""
    rows = []
    for d in range(1, 7):  # 6 unique training days (mix TRUE/MID)
        flag = "TRUE" if d % 2 else "mid"
        rows.append(f"2026-06-{d:02d},lunch,bento,500,25,60,15,{flag},")
    write_diet_log(tmp_path / "diet_log.csv", rows)
    r = run_script("weight-log-append.py", "--dir", str(tmp_path),
                   "--weight", "58.2", "--body-fat-pct", "24", "--date", "2026-06-14")
    assert r.returncode == 0, r.stderr
    assert read_rows(tmp_path / "weight_log.csv")[0]["pal"] == "1.55"


def test_appends_header_once(tmp_path):
    for _ in range(2):
        r = run_script("weight-log-append.py", "--dir", str(tmp_path),
                       "--weight", "58.2", "--body-fat-pct", "24", "--date", "2026-06-14")
        assert r.returncode == 0, r.stderr
    text = (tmp_path / "weight_log.csv").read_text()
    assert text.count("date,height_cm") == 1
    assert len(read_rows(tmp_path / "weight_log.csv")) == 2


def test_no_body_fat_and_no_profile_errors(tmp_path):
    r = run_script("weight-log-append.py", "--dir", str(tmp_path),
                   "--weight", "70", "--date", "2026-06-14")
    assert r.returncode != 0
    assert "incomplete profile" in r.stderr


def test_weight_out_of_range_errors(tmp_path):
    r = run_script("weight-log-append.py", "--dir", str(tmp_path),
                   "--weight", "500", "--body-fat-pct", "24", "--date", "2026-06-14")
    assert r.returncode != 0
    assert "out of range" in r.stderr


def test_bad_date_errors(tmp_path):
    r = run_script("weight-log-append.py", "--dir", str(tmp_path),
                   "--weight", "58.2", "--body-fat-pct", "24", "--date", "junk")
    assert r.returncode != 0
    assert "not valid YYYY-MM-DD" in r.stderr
