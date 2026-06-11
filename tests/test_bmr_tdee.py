"""Tests for scripts/bmr-tdee.py."""
from conftest import run_script


def test_happy_mifflin_female():
    r = run_script("bmr-tdee.py", "--weight", "55", "--height", "160", "--age", "30", "--gender", "female")
    assert r.returncode == 0
    assert "Mifflin-St Jeor (female)" in r.stdout
    assert "BMR: " in r.stdout
    assert "TDEE: " in r.stdout


def test_happy_mifflin_male():
    r = run_script("bmr-tdee.py", "--weight", "70", "--height", "175", "--age", "35", "--gender", "male")
    assert r.returncode == 0
    assert "Mifflin-St Jeor (male)" in r.stdout


def test_happy_katch_mcardle_overrides_gender():
    """Body-fat-pct triggers Katch-McArdle; gender becomes irrelevant."""
    r = run_script(
        "bmr-tdee.py", "--weight", "55", "--height", "160", "--age", "30",
        "--gender", "female", "--body-fat-pct", "25",
    )
    assert r.returncode == 0
    assert "Katch-McArdle" in r.stdout


def test_custom_pal():
    r = run_script(
        "bmr-tdee.py", "--weight", "55", "--height", "160", "--age", "30",
        "--gender", "female", "--pal", "1.725",
    )
    assert r.returncode == 0
    assert "PAL 1.725" in r.stdout


def test_error_weight_out_of_range():
    r = run_script("bmr-tdee.py", "--weight", "5", "--height", "160", "--age", "30", "--gender", "female")
    assert r.returncode == 1
    assert "out of range" in r.stderr
    assert "weight" in r.stderr


def test_error_body_fat_too_high():
    r = run_script(
        "bmr-tdee.py", "--weight", "55", "--height", "160", "--age", "30",
        "--gender", "female", "--body-fat-pct", "90",
    )
    assert r.returncode == 1
    assert "body-fat-pct" in r.stderr


def test_error_pal_out_of_range():
    r = run_script(
        "bmr-tdee.py", "--weight", "55", "--height", "160", "--age", "30",
        "--gender", "female", "--pal", "0.5",
    )
    assert r.returncode == 1
    assert "pal" in r.stderr


def test_error_missing_required_arg_argparse():
    """argparse rejects missing required arg with exit 2."""
    r = run_script("bmr-tdee.py", "--weight", "55")
    assert r.returncode == 2
    assert "required" in r.stderr or "the following arguments" in r.stderr
