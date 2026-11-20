"""Week 2 checks for starter/chatbot.py. Run with `make check WEEK=2`.

The model is faked (fake_llm): each test queues what the "model" replies, then checks what
your chatbot sent and what it kept. No real calls, no free requests used.
"""

import logging
from collections.abc import Callable
from types import ModuleType

import pytest

from exercises.common.testing import FakeClient, api_error, rate_limit_error


@pytest.fixture
def bot(load_starter: Callable[[str], ModuleType]) -> ModuleType:
    module = load_starter("chatbot")
    module.SESSIONS.clear()
    return module


def _turns(n: int) -> list[dict[str, str]]:
    """n finished turns: user/assistant pairs numbered from 1."""
    messages: list[dict[str, str]] = []
    for i in range(1, n + 1):
        messages.append({"role": "user", "content": f"question {i}"})
        messages.append({"role": "assistant", "content": f"answer {i}"})
    return messages


# --- sessions and memory -----------------------------------------------------------


def test_system_prompt_is_written(bot: ModuleType) -> None:
    assert isinstance(bot.SYSTEM_PROMPT, str)
    assert "TODO" not in bot.SYSTEM_PROMPT
    assert "Octech Help" in bot.SYSTEM_PROMPT


def test_new_session_ids_are_unique(bot: ModuleType) -> None:
    first, second = bot.new_session(), bot.new_session()

    assert isinstance(first, str) and first
    assert first != second
    assert first in bot.SESSIONS and second in bot.SESSIONS


def test_reply_sends_system_prompt_and_returns_model_reply(
    bot: ModuleType, fake_llm: FakeClient
) -> None:
    session = bot.new_session()
    fake_llm.queue("Hello! How can I help?")

    assert bot.reply(session, "Hi") == "Hello! How can I help?"
    assert fake_llm.last_messages == [
        {"role": "system", "content": bot.SYSTEM_PROMPT},
        {"role": "user", "content": "Hi"},
    ]


def test_history_is_resent_every_turn(bot: ModuleType, fake_llm: FakeClient) -> None:
    session = bot.new_session()
    fake_llm.queue("Nice to meet you, Amina.", "Your name is Amina.")

    bot.reply(session, "My name is Amina.")
    bot.reply(session, "What is my name?")

    assert fake_llm.last_messages == [
        {"role": "system", "content": bot.SYSTEM_PROMPT},
        {"role": "user", "content": "My name is Amina."},
        {"role": "assistant", "content": "Nice to meet you, Amina."},
        {"role": "user", "content": "What is my name?"},
    ]


def test_sessions_are_separate(bot: ModuleType, fake_llm: FakeClient) -> None:
    amina, brian = bot.new_session(), bot.new_session()
    fake_llm.queue("Hi Amina.", "Hello.")

    bot.reply(amina, "I am Amina.")
    bot.reply(brian, "Hello there.")

    assert fake_llm.last_messages == [
        {"role": "system", "content": bot.SYSTEM_PROMPT},
        {"role": "user", "content": "Hello there."},
    ]


def test_unknown_session_raises_key_error(bot: ModuleType, fake_llm: FakeClient) -> None:
    with pytest.raises(KeyError):
        bot.reply("no-such-session", "Hi")
    assert fake_llm.calls == []


# --- trimming ------------------------------------------------------------------------


def test_trim_history_keeps_system_and_last_turns(bot: ModuleType) -> None:
    system = {"role": "system", "content": "rules"}
    messages = [system, *_turns(10), {"role": "user", "content": "question 11"}]
    original = list(messages)

    trimmed = bot.trim_history(messages, max_turns=3)

    assert trimmed == [
        system,
        {"role": "user", "content": "question 9"},
        {"role": "assistant", "content": "answer 9"},
        {"role": "user", "content": "question 10"},
        {"role": "assistant", "content": "answer 10"},
        {"role": "user", "content": "question 11"},
    ]
    assert messages == original, "trim_history must return a new list, not change its input"


def test_trim_history_leaves_short_history_alone(bot: ModuleType) -> None:
    messages = [{"role": "system", "content": "rules"}, *_turns(2)]

    assert bot.trim_history(messages, max_turns=6) == messages


def test_long_conversation_is_capped(bot: ModuleType, fake_llm: FakeClient) -> None:
    session = bot.new_session()
    for i in range(1, 11):
        fake_llm.queue(f"answer {i}")
        bot.reply(session, f"question {i}")

    sent = fake_llm.last_messages
    assert sent[0] == {"role": "system", "content": bot.SYSTEM_PROMPT}
    assert sent[-1] == {"role": "user", "content": "question 10"}
    assert len(sent) == 1 + 2 * bot.MAX_TURNS - 1, "system prompt + the last MAX_TURNS turns"
    assert sent[1]["role"] == "user"


# --- validation and failures ---------------------------------------------------------


@pytest.mark.parametrize("text", ["", "   ", "x" * 2001])
def test_bad_messages_are_rejected(bot: ModuleType, fake_llm: FakeClient, text: str) -> None:
    session = bot.new_session()

    with pytest.raises(ValueError):
        bot.reply(session, text)
    assert fake_llm.calls == []


def test_failed_model_call_returns_fallback_and_saves_nothing(
    bot: ModuleType, fake_llm: FakeClient
) -> None:
    session = bot.new_session()
    fake_llm.queue(rate_limit_error(), rate_limit_error(), rate_limit_error(), "Back again.")

    assert bot.reply(session, "Are you there?") == bot.FALLBACK_REPLY
    bot.reply(session, "Hello?")

    assert fake_llm.last_messages == [
        {"role": "system", "content": bot.SYSTEM_PROMPT},
        {"role": "user", "content": "Hello?"},
    ], "a failed turn must not be saved"


def test_any_model_error_returns_fallback(bot: ModuleType, fake_llm: FakeClient) -> None:
    """Not just rate limits: a provider error must not crash the chat either."""
    session = bot.new_session()
    fake_llm.queue(api_error("Upstream provider error"))

    assert bot.reply(session, "Hello?") == bot.FALLBACK_REPLY


# --- streaming -----------------------------------------------------------------------


def test_reply_stream_yields_pieces_and_saves_full_reply(
    bot: ModuleType, fake_llm: FakeClient
) -> None:
    session = bot.new_session()
    fake_llm.queue_stream(["Your file ", "is in ", "Registry."])
    fake_llm.queue("ok")

    pieces = list(bot.reply_stream(session, "Where is my file?"))
    bot.reply(session, "Thanks")

    assert pieces == ["Your file ", "is in ", "Registry."]
    assert fake_llm.calls[0]["stream"] is True
    assert fake_llm.last_messages[-2:] == [
        {"role": "assistant", "content": "Your file is in Registry."},
        {"role": "user", "content": "Thanks"},
    ]


def test_failed_stream_yields_fallback_and_saves_nothing(
    bot: ModuleType, fake_llm: FakeClient
) -> None:
    session = bot.new_session()
    fake_llm.queue_stream(["Half an ans", rate_limit_error()])
    fake_llm.queue("ok")

    pieces = list(bot.reply_stream(session, "Where is my file?"))
    bot.reply(session, "Hello?")

    assert pieces == ["Half an ans", bot.FALLBACK_REPLY]
    assert fake_llm.last_messages == [
        {"role": "system", "content": bot.SYSTEM_PROMPT},
        {"role": "user", "content": "Hello?"},
    ], "neither the question nor the half answer may be saved"


def test_reply_stream_checks_before_streaming(bot: ModuleType, fake_llm: FakeClient) -> None:
    """Errors must come from the call itself, before any piece is read."""
    session = bot.new_session()

    with pytest.raises(ValueError):
        bot.reply_stream(session, "   ")
    with pytest.raises(KeyError):
        bot.reply_stream("no-such-session", "Hi")
    assert fake_llm.calls == []


def test_user_messages_are_never_logged(
    bot: ModuleType,
    fake_llm: FakeClient,
    caplog: pytest.LogCaptureFixture,
    capsys: pytest.CaptureFixture[str],
) -> None:
    caplog.set_level(logging.DEBUG)
    session = bot.new_session()
    fake_llm.queue("Noted.")
    fake_llm.queue_stream(["Noted ", "again."])

    bot.reply(session, "My ID is CM-FAKE-4827-KR")
    list(bot.reply_stream(session, "My phone is 0700 000 001"))

    printed = capsys.readouterr()
    for secret in ("CM-FAKE-4827-KR", "0700 000 001"):
        assert secret not in caplog.text, "user text must not be logged"
        assert secret not in printed.out + printed.err, "user text must not be printed"
