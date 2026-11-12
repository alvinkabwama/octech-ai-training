"""The pre-push hook must block pushes to main and allow everything else."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[2] / "scripts" / "hooks" / "pre-push"
SHA = "a" * 40

pytestmark = pytest.mark.skipif(shutil.which("sh") is None, reason="needs a POSIX sh")


def _push(remote_ref: str, **env: str) -> subprocess.CompletedProcess[str]:
    line = f"refs/heads/x {SHA} {remote_ref} {SHA}\n"
    return subprocess.run(
        ["sh", str(HOOK)],
        input=line,
        capture_output=True,
        text=True,
        env={**os.environ, **env},
        check=False,
    )


def test_blocks_push_to_main() -> None:
    result = _push("refs/heads/main")
    assert result.returncode == 1
    assert "can't push to main" in result.stderr


def test_allows_trainee_branches() -> None:
    assert _push("refs/heads/trainee/rachel").returncode == 0
    assert _push("refs/heads/trainee/rachel-week-1").returncode == 0


def test_trainer_override() -> None:
    assert _push("refs/heads/main", ALLOW_MAIN_PUSH="1").returncode == 0
