"""Tests for scripts/food-ref-append.py."""
import os
from conftest import run_script, write_food_ref


def _env_with_csv(path):
    env = os.environ.copy()
    env["DIET_COACH_FOOD_REF"] = str(path)
    return env


def test_happy_append(tmp_path):
    csv = tmp_path / "food_reference.csv"
    write_food_ref(csv, [])
    r = run_script(
        "food-ref-append.py",
        "--food-name", "test豆漿", "--source", "統一",
        "--serving-size-g", "400", "--calories", "167",
        "--protein-g", "15", "--carb-g", "14", "--fat-g", "7.6",
        "--notes", "test",
        env=_env_with_csv(csv),
    )
    assert r.returncode == 0
    assert "appended" in r.stdout
    assert "test豆漿" in csv.read_text()


def test_duplicate_skip(tmp_path):
    csv = tmp_path / "food_reference.csv"
    write_food_ref(csv, [])
    args = [
        "--food-name", "test豆漿", "--source", "統一",
        "--serving-size-g", "400", "--calories", "167",
        "--protein-g", "15", "--carb-g", "14", "--fat-g", "7.6",
        "--notes", "test",
    ]
    run_script("food-ref-append.py", *args, env=_env_with_csv(csv))
    r2 = run_script("food-ref-append.py", *args, env=_env_with_csv(csv))
    assert r2.returncode == 0
    assert "skipped (duplicate)" in r2.stdout


def test_error_negative_calories(tmp_path):
    csv = tmp_path / "food_reference.csv"
    write_food_ref(csv, [])
    r = run_script(
        "food-ref-append.py",
        "--food-name", "x", "--source", "y",
        "--serving-size-g", "100", "--calories", "-50",
        "--protein-g", "5", "--carb-g", "10", "--fat-g", "2", "--notes", "",
        env=_env_with_csv(csv),
    )
    assert r.returncode == 1
    assert "calories" in r.stderr
    assert ">= 0" in r.stderr


def test_error_non_numeric_protein(tmp_path):
    csv = tmp_path / "food_reference.csv"
    write_food_ref(csv, [])
    r = run_script(
        "food-ref-append.py",
        "--food-name", "x", "--source", "y",
        "--serving-size-g", "100", "--calories", "200",
        "--protein-g", "abc", "--carb-g", "10", "--fat-g", "2", "--notes", "",
        env=_env_with_csv(csv),
    )
    assert r.returncode == 1
    assert "not a number" in r.stderr


def test_error_missing_csv(tmp_path):
    nonexistent = tmp_path / "nope.csv"
    r = run_script(
        "food-ref-append.py",
        "--food-name", "x", "--source", "y",
        "--serving-size-g", "100", "--calories", "200",
        "--protein-g", "5", "--carb-g", "10", "--fat-g", "2", "--notes", "",
        env=_env_with_csv(nonexistent),
    )
    assert r.returncode == 1
    assert "not found" in r.stderr
