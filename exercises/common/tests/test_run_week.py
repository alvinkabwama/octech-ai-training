"""Tests for scripts/run_week.py (make check / make live)."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

RUN_WEEK = Path(__file__).resolve().parents[3] / "scripts" / "run_week.py"


@pytest.fixture(scope="module")
def run_week() -> ModuleType:
    spec = importlib.util.spec_from_file_location("run_week", RUN_WEEK)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_week(root: Path, name: str, test_body: str) -> Path:
    week = root / name
    (week / "tests").mkdir(parents=True)
    (week / "starter").mkdir()
    (week / "tests" / f"test_{name.replace('-', '_')}.py").write_text(
        f"def test_it():\n    {test_body}\n", encoding="utf-8"
    )
    (week / "starter" / "live.py").write_text("print('live ran')\n", encoding="utf-8")
    return week


def test_week_dir_finds_week_by_number(run_week: ModuleType, tmp_path: Path) -> None:
    week = _make_week(tmp_path, "week-1-calling-a-model", "pass")
    _make_week(tmp_path, "week-10-later", "pass")

    assert run_week.week_dir(1, tmp_path) == week


def test_unknown_week_lists_available(run_week: ModuleType, tmp_path: Path) -> None:
    _make_week(tmp_path, "week-0-git-and-setup", "pass")

    with pytest.raises(run_week.WeekNotFound, match="week-0-git-and-setup"):
        run_week.week_dir(7, tmp_path)


def test_check_command_targets_week_tests(run_week: ModuleType, tmp_path: Path) -> None:
    week = _make_week(tmp_path, "week-2-chatbot", "pass")

    command, env = run_week.check_command(2, None, tmp_path)

    assert command == [sys.executable, "-m", "pytest", str(week / "tests")]
    assert run_week.STARTER_ENV not in env


def test_check_command_passes_starter_override(run_week: ModuleType, tmp_path: Path) -> None:
    _make_week(tmp_path, "week-2-chatbot", "pass")
    solution = tmp_path / "solutions" / "week-2"
    solution.mkdir(parents=True)

    _command, env = run_week.check_command(2, solution, tmp_path)

    assert env[run_week.STARTER_ENV] == str(solution.resolve())


def test_live_command_runs_starter_live_script(run_week: ModuleType, tmp_path: Path) -> None:
    week = _make_week(tmp_path, "week-0-git-and-setup", "pass")

    assert run_week.live_command(0, None, tmp_path) == [
        sys.executable,
        str(week / "starter" / "live.py"),
    ]


def test_live_command_with_override(run_week: ModuleType, tmp_path: Path) -> None:
    _make_week(tmp_path, "week-0-git-and-setup", "pass")
    solution = tmp_path / "sol"
    solution.mkdir()
    (solution / "live.py").write_text("", encoding="utf-8")

    command = run_week.live_command(0, solution, tmp_path)

    assert command[1] == str((solution / "live.py").resolve())


def test_main_returns_pytest_exit_code(run_week: ModuleType, tmp_path: Path) -> None:
    _make_week(tmp_path, "week-3-passing", "assert True")
    _make_week(tmp_path, "week-4-failing", "assert False")

    assert run_week.main(["check", "3"], exercises_root=tmp_path) == 0
    assert run_week.main(["check", "4"], exercises_root=tmp_path) != 0


def test_main_unknown_week_returns_2(
    run_week: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert run_week.main(["check", "9"], exercises_root=tmp_path) == 2
    assert "week-9" in capsys.readouterr().err
