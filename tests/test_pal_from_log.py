"""Tests for scripts/pal-from-log.py."""
from conftest import run_script, write_diet_log


def test_happy_recommends_pal(tmp_path):
    """3 training days in 14-day window → moderate / 1.55 if logged on enough distinct dates."""
    csv = tmp_path / "diet_log.csv"
    rows = []
    for d in range(1, 15):  # 2026-06-01 .. 2026-06-14
        is_training = "TRUE" if d % 3 == 0 else "FALSE"  # 4 training days
        rows.append(f"2026-06-{d:02d},lunch,bento,500,25,60,15,{is_training},")
    write_diet_log(csv, rows)
    r = run_script("pal-from-log.py", "--csv", str(csv), "--today", "2026-06-14")
    assert r.returncode == 0
    assert "recommended PAL:" in r.stdout
    assert "training days: 4" in r.stdout
    assert "window:" in r.stdout


def test_sparse_warning(tmp_path):
    """< 3 unique log dates → sparse warning, still outputs PAL."""
    csv = tmp_path / "diet_log.csv"
    write_diet_log(csv, ["2026-06-10,breakfast,oats,300,10,50,5,TRUE,"])
    r = run_script("pal-from-log.py", "--csv", str(csv), "--today", "2026-06-14")
    assert r.returncode == 0
    assert "data sparse" in r.stdout
    assert "recommended PAL:" in r.stdout  # still outputs


def test_empty_window_no_recommendation(tmp_path):
    """No entries in window → no PAL recommendation, only keep-current hint."""
    csv = tmp_path / "diet_log.csv"
    write_diet_log(csv, ["2026-01-01,breakfast,oats,300,10,50,5,TRUE,"])  # far outside window
    r = run_script("pal-from-log.py", "--csv", str(csv), "--today", "2026-06-14")
    assert r.returncode == 0
    assert "no log entries in window" in r.stdout
    assert "keep current PAL" in r.stdout
    assert "recommended PAL:" not in r.stdout  # critical: no misleading default


def test_error_missing_file(tmp_path):
    r = run_script("pal-from-log.py", "--csv", str(tmp_path / "nope.csv"))
    assert r.returncode == 1
    assert "not found" in r.stderr


def test_error_bad_today(tmp_path):
    csv = tmp_path / "diet_log.csv"
    write_diet_log(csv, [])
    r = run_script("pal-from-log.py", "--csv", str(csv), "--today", "notadate")
    assert r.returncode == 1
    assert "not valid YYYY-MM-DD" in r.stderr


def test_error_bad_days(tmp_path):
    csv = tmp_path / "diet_log.csv"
    write_diet_log(csv, [])
    r = run_script("pal-from-log.py", "--csv", str(csv), "--days", "0")
    assert r.returncode == 1
    assert "must be >= 1" in r.stderr
