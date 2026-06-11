"""Tests for scripts/diet-summary.py."""
from conftest import run_script, write_diet_log


def test_happy_with_entries(tmp_path):
    csv = tmp_path / "diet_log.csv"
    write_diet_log(csv, [
        "2026-06-10,breakfast,oats,300,10,50,5,TRUE,",
        "2026-06-10,lunch,bento,650,30,80,20,TRUE,",
    ])
    r = run_script("diet-summary.py", "--csv", str(csv), "--date", "2026-06-10")
    assert r.returncode == 0
    assert "2026-06-10" in r.stdout
    assert "training day" in r.stdout
    assert "entries: 2" in r.stdout
    assert "950" in r.stdout  # total kcal
    assert "P 40" in r.stdout  # protein


def test_rest_day(tmp_path):
    csv = tmp_path / "diet_log.csv"
    write_diet_log(csv, ["2026-06-10,breakfast,eggs,250,18,2,18,FALSE,"])
    r = run_script("diet-summary.py", "--csv", str(csv), "--date", "2026-06-10")
    assert r.returncode == 0
    assert "rest day" in r.stdout


def test_empty_day(tmp_path):
    csv = tmp_path / "diet_log.csv"
    write_diet_log(csv, [])
    r = run_script("diet-summary.py", "--csv", str(csv), "--date", "2026-06-10")
    assert r.returncode == 0
    assert "當日無記錄" in r.stdout


def test_error_missing_file(tmp_path):
    csv = tmp_path / "nonexistent.csv"
    r = run_script("diet-summary.py", "--csv", str(csv))
    assert r.returncode == 1
    assert "not found" in r.stderr
    assert str(csv) in r.stderr


def test_error_bad_date(tmp_path):
    csv = tmp_path / "diet_log.csv"
    write_diet_log(csv, [])
    r = run_script("diet-summary.py", "--csv", str(csv), "--date", "not-a-date")
    assert r.returncode == 1
    assert "not valid YYYY-MM-DD" in r.stderr


def test_error_missing_columns(tmp_path):
    csv = tmp_path / "broken.csv"
    csv.write_text("date,food\n2026-06-10,oats\n")
    r = run_script("diet-summary.py", "--csv", str(csv), "--date", "2026-06-10")
    assert r.returncode == 1
    assert "missing columns" in r.stderr
