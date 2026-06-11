"""Shared pytest helpers for invoking scripts/*.py as subprocesses."""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"


def run_script(name, *args, env=None, check=False):
    """Run scripts/<name> with args, return CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / name), *args],
        capture_output=True,
        text=True,
        env=env,
        check=check,
    )


DIET_LOG_HEADER = "date,meal_type,food,calories,protein_g,carb_g,fat_g,training_day,notes"
FOOD_REF_HEADER = "food_name,source,serving_size_g,calories,protein_g,carb_g,fat_g,notes"


def write_diet_log(path, rows):
    path.write_text(DIET_LOG_HEADER + "\n" + "\n".join(rows) + ("\n" if rows else ""))


def write_food_ref(path, rows):
    path.write_text(FOOD_REF_HEADER + "\n" + "\n".join(rows) + ("\n" if rows else ""))
