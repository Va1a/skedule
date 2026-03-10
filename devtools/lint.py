import subprocess
import sys


TARGETS = [
    "skedule",
    "devtools",
    "tests",
    "main.py",
    "run.py",
]


def run_flake8(*args: str) -> int:
    result = subprocess.run(
        [sys.executable, "-m", "flake8", *TARGETS, *args],
        check=False,
    )
    return result.returncode


def main() -> int:
    fatal_code = run_flake8(
        "--count",
        "--select=E9,F63,F7,F82",
        "--extend-ignore=W191",
        "--show-source",
        "--statistics",
    )
    if fatal_code != 0:
        return fatal_code

    return run_flake8(
        "--count",
        "--max-complexity=10",
        "--max-line-length=127",
        "--extend-ignore=W191",
        "--statistics",
    )
