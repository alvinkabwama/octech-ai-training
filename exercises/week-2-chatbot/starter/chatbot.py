"""Week 2: a chatbot with memory. Replace each TODO, then run `make check WEEK=2`.

The model forgets everything between calls, so this module remembers for it: each
session keeps its own message list, and every turn sends that list (trimmed) again.

    session = new_session()
    reply(session, "Hi, I'm Amina.")              # full answer at once
    for piece in reply_stream(session, "Who am I?"):  # answer piece by piece
        print(piece, end="")

Read LESSON.md first. The tests fake the model, so `make check` costs no free requests.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import openai  # noqa: F401  (for openai.APIError, see reply())

from exercises.common import llm  # noqa: F401  (you'll use llm.chat / llm.chat_stream below)

MAX_MESSAGE_CHARS = 2000
MAX_TURNS = 6
FALLBACK_REPLY = "Sorry, I couldn't answer that just now. Please try again in a minute."

# TODO: write the system prompt for "Octech Help", a fictional assistant that answers
# questions about Octech's products in plain words. Say what it should do when it doesn't
# know, and keep answers short. It must contain the words "Octech Help".
SYSTEM_PROMPT = (
    "You are Octech Help, a friendly assistant that answers questions about Octech's "
    "products in plain words. Keep answers short, at most 3 sentences. If you don't "
    "know the answer, say so honestly and suggest contacting the Octech support team. "
    "Never make up product details."
)


class UnknownSessionError(KeyError):
    """No session with this id (never created, or already ended)."""


# The in-memory store: session id -> that conversation's messages (system prompt first).
# Everything here is lost when the process stops. That's fine for this week.
SESSIONS: dict[str, list[dict[str, str]]] = {}


def new_session() -> str:
    """Start a conversation and return its id."""
    session_id = uuid.uuid4().hex
    SESSIONS[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return session_id


def end_session(session_id: str) -> None:
    """Forget a conversation."""
    if session_id not in SESSIONS:
        raise UnknownSessionError(session_id)
    del SESSIONS[session_id]


def trim_history(
    messages: list[dict[str, str]], max_turns: int = MAX_TURNS
) -> list[dict[str, str]]:
    """Keep the system message(s) plus only the last ``max_turns`` turns."""
    system = [m for m in messages if m["role"] == "system"]
    rest = [m for m in messages if m["role"] != "system"]
    user_positions = [i for i, m in enumerate(rest) if m["role"] == "user"]
    if len(user_positions) > max_turns:
        rest = rest[user_positions[-max_turns] :]
    return system + rest


def _check_and_build(session_id: str, text: str) -> tuple[str, list[dict[str, str]]]:
    """Validate the message and session; return the clean text and messages to send."""
    text = text.strip()
    if not text or len(text) > MAX_MESSAGE_CHARS:
        raise ValueError(f"message must be 1 to {MAX_MESSAGE_CHARS} characters")
    if session_id not in SESSIONS:
        raise UnknownSessionError(session_id)
    messages = trim_history([*SESSIONS[session_id], {"role": "user", "content": text}])
    return text, messages


def reply(session_id: str, text: str) -> str:
    """Answer ``text`` in this session and remember the turn."""
    _, messages = _check_and_build(session_id, text)
    try:
        answer = llm.chat(messages)
    except (llm.LLMError, openai.APIError):
        return FALLBACK_REPLY
    SESSIONS[session_id] = trim_history([*messages, {"role": "assistant", "content": answer}])
    return answer


def reply_stream(session_id: str, text: str) -> Iterator[str]:
    """Like :func:`reply`, but yields the answer piece by piece as the model writes it."""
    # These checks run NOW, when reply_stream() is called, before any streaming starts.
    _, messages = _check_and_build(session_id, text)

    def pieces() -> Iterator[str]:
        collected: list[str] = []
        try:
            for piece in llm.chat_stream(messages):
                collected.append(piece)
                yield piece
        except (llm.LLMError, openai.APIError):
            yield FALLBACK_REPLY
            return  # save nothing: not the question, not the half-written answer
        answer = "".join(collected)
        SESSIONS[session_id] = trim_history([*messages, {"role": "assistant", "content": answer}])

    return pieces()
