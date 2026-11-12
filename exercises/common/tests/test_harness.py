"""Tests for the exercise test harness in exercises/conftest.py."""

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import openai
import pytest

from exercises.common import llm
from exercises.common.testing import FakeClient


def test_real_openai_client_is_blocked_in_tests() -> None:
    with pytest.raises(RuntimeError, match="must not call a real model"):
        openai.OpenAI(api_key="sk-or-v1-not-real", base_url=llm.OPENROUTER_BASE_URL)


def test_fake_llm_answers_ask_and_chat(fake_llm: FakeClient) -> None:
    fake_llm.queue("one", "two")

    assert llm.ask("first") == "one"
    assert llm.chat([{"role": "user", "content": "second"}]) == "two"
    assert fake_llm.last_messages == [{"role": "user", "content": "second"}]


def test_fake_llm_catches_imported_names(fake_llm: FakeClient) -> None:
    """A starter doing `from exercises.common.llm import ask` still hits the fake."""
    from exercises.common.llm import ask

    fake_llm.queue("stubbed")

    assert ask("hello") == "stubbed"


def test_load_starter_uses_override_dir(
    load_starter: Callable[[str], ModuleType],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "sample_mod.py").write_text("VALUE = 42\n", encoding="utf-8")
    monkeypatch.setenv("EXERCISE_STARTER_DIR", str(tmp_path))

    module = load_starter("sample_mod")

    assert module.VALUE == 42


def test_load_starter_missing_module_explains(
    load_starter: Callable[[str], ModuleType],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EXERCISE_STARTER_DIR", str(tmp_path))

    with pytest.raises(FileNotFoundError, match="nothing_here.py"):
        load_starter("nothing_here")
