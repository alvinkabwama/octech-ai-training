"""The demo script drives upload -> ocr -> file -> route through the HTTP API."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
from fastapi.testclient import TestClient

from mini_edrms.app.main import create_app

DEMO_PATH = Path(__file__).resolve().parents[2] / "scripts" / "demo.py"


def _load_demo() -> ModuleType:
    spec = importlib.util.spec_from_file_location("demo", DEMO_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_demo_runs_full_flow(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    demo = _load_demo()

    with TestClient(create_app(tmp_path)) as client:
        rows = demo.run(client)

    actions = [row["action"] for row in rows]
    assert actions.count("upload") == 3
    assert actions.count("ocr") == 3
    assert actions.count("file") == 3
    assert actions.count("route") == 3
    output = capsys.readouterr().out
    for action in ("upload", "ocr", "file", "route"):
        assert action in output


def test_demo_reports_server_not_running(capsys: pytest.CaptureFixture[str]) -> None:
    demo = _load_demo()

    exit_code = demo.main(["--base-url", "http://127.0.0.1:9"])

    assert exit_code == 1
    assert "make run" in capsys.readouterr().err
