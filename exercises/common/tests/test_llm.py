"""Tests for the shared OpenRouter helper. A fake client stands in for the network."""

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import openai
import pytest

from exercises.common import llm
from exercises.common.testing import FakeClient, rate_limit_error


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeClient:
    client = FakeClient()
    monkeypatch.setattr(llm, "get_client", lambda: client)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)
    return client


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    recorded: list[float] = []
    monkeypatch.setattr(llm.time, "sleep", recorded.append)
    return recorded


@pytest.fixture
def no_env_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[None]:
    """Point the helper at a .env that doesn't exist, so the real one can't leak in."""
    monkeypatch.setattr(llm, "ENV_FILE", tmp_path / "missing.env")
    llm.get_client.cache_clear()
    yield
    llm.get_client.cache_clear()


def test_chat_sends_fallback_models_and_returns_content(fake: FakeClient) -> None:
    fake.queue("Hello!")

    reply = llm.chat([{"role": "user", "content": "Hi"}])

    assert reply == "Hello!"
    call = fake.calls[0]
    assert call["extra_body"] == {"models": llm.DEFAULT_MODELS}
    assert call["model"] == llm.DEFAULT_MODELS[0]
    assert call["messages"] == [{"role": "user", "content": "Hi"}]
    assert call["temperature"] == 0.3


def test_default_models() -> None:
    assert llm.DEFAULT_MODELS == [
        "openrouter/free",
        "google/gemma-4-31b-it:free",
        "nvidia/nemotron-3.5-lightning:free",
    ]


def test_env_model_overrides_first_entry(fake: FakeClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_MODEL", "liquid/lfm-3-1.7b:free")
    fake.queue("ok")

    llm.chat([{"role": "user", "content": "Hi"}])

    assert fake.calls[0]["extra_body"]["models"] == [
        "liquid/lfm-3-1.7b:free",
        "google/gemma-4-31b-it:free",
        "nvidia/nemotron-3.5-lightning:free",
    ]
    assert fake.calls[0]["model"] == "liquid/lfm-3-1.7b:free"
    assert llm.DEFAULT_MODELS[0] == "openrouter/free", "the constant must not be mutated"


def test_model_argument_goes_first_without_duplicates(fake: FakeClient) -> None:
    fake.queue("ok")

    llm.chat([{"role": "user", "content": "Hi"}], model="nvidia/nemotron-3.5-lightning:free")

    models = fake.calls[0]["extra_body"]["models"]
    assert models[0] == "nvidia/nemotron-3.5-lightning:free"
    assert len(models) == len(set(models)) <= llm.MAX_MODELS


def test_extra_kwargs_are_passed_through(fake: FakeClient) -> None:
    fake.queue("ok")

    llm.chat([{"role": "user", "content": "Hi"}], temperature=0, max_tokens=50)

    assert fake.calls[0]["temperature"] == 0
    assert fake.calls[0]["max_tokens"] == 50


def test_retries_on_429_then_succeeds(fake: FakeClient, sleeps: list[float]) -> None:
    fake.queue(rate_limit_error(), "finally")

    assert llm.chat([{"role": "user", "content": "Hi"}]) == "finally"
    assert len(fake.calls) == 2
    assert sleeps == [5]


def test_gives_up_after_3_tries(fake: FakeClient, sleeps: list[float]) -> None:
    fake.queue(rate_limit_error(), rate_limit_error(), rate_limit_error(), "never used")

    with pytest.raises(llm.LLMError, match="(?i)rate limit"):
        llm.chat([{"role": "user", "content": "Hi"}])

    assert len(fake.calls) == 3
    assert sleeps == [5, 10]


def test_other_api_errors_are_not_retried(fake: FakeClient, sleeps: list[float]) -> None:
    import httpx

    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    error = openai.AuthenticationError(
        "bad key", response=httpx.Response(401, request=request), body=None
    )
    fake.queue(error)

    with pytest.raises(openai.AuthenticationError):
        llm.chat([{"role": "user", "content": "Hi"}])
    assert sleeps == []


def test_empty_reply_raises(fake: FakeClient) -> None:
    fake.queue(None)

    with pytest.raises(llm.LLMError, match="(?i)empty"):
        llm.chat([{"role": "user", "content": "Hi"}])


def test_ask_sends_system_and_user(fake: FakeClient) -> None:
    fake.queue("Oli otya!")

    reply = llm.ask("Say hello in Luganda", system="Be brief.", temperature=0)

    assert reply == "Oli otya!"
    assert fake.calls[0]["messages"] == [
        {"role": "system", "content": "Be brief."},
        {"role": "user", "content": "Say hello in Luganda"},
    ]
    assert fake.calls[0]["temperature"] == 0


def test_ask_without_system_sends_only_user(fake: FakeClient) -> None:
    fake.queue("hi")

    llm.ask("Hello")

    assert fake.calls[0]["messages"] == [{"role": "user", "content": "Hello"}]


def test_missing_key_error_names_variable_and_env_example(
    monkeypatch: pytest.MonkeyPatch, no_env_file: None
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(llm.LLMError) as exc:
        llm.get_client()

    message = str(exc.value)
    assert "OPENROUTER_API_KEY" in message
    assert ".env.example" in message


def test_get_client_points_at_openrouter(
    monkeypatch: pytest.MonkeyPatch, no_env_file: None
) -> None:
    created: list[dict[str, Any]] = []

    class Recorder:
        def __init__(self, **kwargs: Any) -> None:
            created.append(kwargs)

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-test-not-real")
    monkeypatch.setattr(openai, "OpenAI", Recorder)

    llm.get_client()

    assert created[0]["base_url"] == "https://openrouter.ai/api/v1"
    assert created[0]["api_key"] == "sk-or-v1-test-not-real"
    assert created[0]["max_retries"] == 0, "our retry loop must be the only one"


def test_get_client_reads_key_from_env_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    created: list[dict[str, Any]] = []

    class Recorder:
        def __init__(self, **kwargs: Any) -> None:
            created.append(kwargs)

    env_file = tmp_path / ".env"
    env_file.write_text("OPENROUTER_API_KEY=sk-or-v1-from-file\n", encoding="utf-8")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setattr(llm, "ENV_FILE", env_file)
    monkeypatch.setattr(openai, "OpenAI", Recorder)
    llm.get_client.cache_clear()
    try:
        llm.get_client()
    finally:
        llm.get_client.cache_clear()
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    assert created[0]["api_key"] == "sk-or-v1-from-file"
