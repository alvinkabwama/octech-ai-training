"""Run one week's exercise tests, or its live script against OpenRouter.

    python scripts/run_week.py check 1        # = make check WEEK=1 (stubbed, no model calls)
    python scripts/run_week.py live 1         # = make live WEEK=1  (real OpenRouter calls)
    python scripts/run_week.py check 1 --starter solutions/week-1   # trainer: check a solution

Week folders are ``exercises/week-<N>-<topic>/`` with ``starter/`` and ``tests/``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXERCISES_ROOT = ROOT / "exercises"
STARTER_ENV = "EXERCISE_STARTER_DIR"


class WeekNotFound(LookupError):
    """No ``week-<N>-*`` folder exists for the requested week."""


def week_dir(week: int, exercises_root: Path = EXERCISES_ROOT) -> Path:
    """Return ``exercises/week-<week>-<topic>``."""
    matches = sorted(exercises_root.glob(f"week-{week}-*"))
    if len(matches) != 1:
        available = ", ".join(p.name for p in sorted(exercises_root.glob("week-*"))) or "none"
        raise WeekNotFound(f"No single folder for week-{week}-*. Available: {available}")
    return matches[0]


def check_command(
    week: int, starter: Path | None, exercises_root: Path = EXERCISES_ROOT
) -> tuple[list[str], dict[str, str]]:
    """The pytest command (and environment) for one week's tests."""
    tests = week_dir(week, exercises_root) / "tests"
    env = {k: v for k, v in os.environ.items() if k != STARTER_ENV}
    if starter is not None:
        env[STARTER_ENV] = str(starter.resolve())
    return [sys.executable, "-m", "pytest", str(tests)], env


def live_command(
    week: int, starter: Path | None, exercises_root: Path = EXERCISES_ROOT
) -> list[str]:
    """The command that runs the week's ``live.py`` (real model calls)."""
    folder = (
        starter.resolve() if starter is not None else week_dir(week, exercises_root) / "starter"
    )
    return [sys.executable, str(folder / "live.py")]


def main(argv: list[str] | None = None, exercises_root: Path = EXERCISES_ROOT) -> int:
    parser = argparse.ArgumentParser(description="Check or live-run one week's exercise.")
    parser.add_argument("action", choices=("check", "live"))
    parser.add_argument("week", type=int, help="week number, e.g. 1")
    parser.add_argument("--starter", type=Path, help="use this folder instead of starter/")
    args = parser.parse_args(argv)

    try:
        if args.action == "check":
            command, env = check_command(args.week, args.starter, exercises_root)
        else:
            command, env = live_command(args.week, args.starter, exercises_root), None
    except WeekNotFound as error:
        print(error, file=sys.stderr)
        return 2
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
