"""Test harness for every exercise. Guarantees tests never call a real model.

Fixtures:
    fake_llm      A scripted FakeClient behind ``llm.get_client``. Queue replies with
                  ``fake_llm.queue("reply", ...)``; inspect ``fake_llm.calls``.
    load_starter  ``load_starter("prompts")`` imports ``<week>/starter/prompts.py``
                  (or the folder in EXERCISE_STARTER_DIR, used to check solutions).
"""

from __future__ import annotations

import importlib.util
import os
import re
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType
from typing import Any

import openai
import pytest

from exercises.common import llm
from exercises.common.testing import FakeClient

STARTER_ENV = "EXERCISE_STARTER_DIR"


class _NoNetworkClient:
    """Replaces openai.OpenAI during tests so nothing can reach OpenRouter."""

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        raise RuntimeError(
            "Tests must not call a real model. Use the fake_llm fixture "
            "(see exercises/conftest.py)."
        )


@pytest.fixture(autouse=True)
def _block_real_model_calls(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    real_get_client = llm.get_client  # other fixtures may replace it with a fake
    monkeypatch.setattr(openai, "OpenAI", _NoNetworkClient)
    real_get_client.cache_clear()
    yield
    real_get_client.cache_clear()


@pytest.fixture
def fake_llm(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    """A scripted model: every llm.chat / llm.ask call is answered from its queue."""
    client = FakeClient()
    monkeypatch.setattr(llm, "get_client", lambda: client)
    monkeypatch.setattr(llm.time, "sleep", lambda _seconds: None)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    return client


@pytest.fixture
def load_starter(request: pytest.FixtureRequest) -> Callable[[str], ModuleType]:
    """Return a loader that imports a module from this week's starter folder."""
    test_file = Path(str(request.path))
    week = test_file.parents[1]

    def load(name: str) -> ModuleType:
        override = os.environ.get(STARTER_ENV)
        starter = Path(override) if override else week / "starter"
        path = starter / f"{name}.py"
        if not path.is_file():
            raise FileNotFoundError(f"Expected {path} (is the file name right?)")
        module_name = re.sub(r"\W", "_", f"_starter_{week.name}_{name}")
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import {path}")
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    return load
