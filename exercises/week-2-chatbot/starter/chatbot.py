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

import openai

from exercises.common import llm

MAX_MESSAGE_CHARS = 2000
MAX_TURNS = 6
FALLBACK_REPLY = "Sorry, I couldn't answer that just now. Please try again in a minute."

# TODO: write the system prompt for "Octech Help", a fictional assistant that answers
# questions about Octech's products in plain words. Say what it should do when it doesn't
# know, and keep answers short. It must contain the words "Octech Help".
SYSTEM_PROMPT = (
    "You are Octech Help, the assistant for Octech's records-management products. "
    "Answer in plain words, with three short sentences at most. "
    "Only answer questions about Octech's products and records management. "
    "If you don't know something, or it is outside that scope, say so briefly "
    "and suggest contacting Octech support. Never invent product features, "
    "prices or policies."
)


class UnknownSessionError(KeyError):
    """No session with this id (never created, or already ended)."""


# The in-memory store: session id -> that conversation's messages (system prompt first).
# Everything here is lost when the process stops. That's fine for this week.
SESSIONS: dict[str, list[dict[str, str]]] = {}


def new_session() -> str:
    """Start a conversation and return its id.

    TODO:
      1. Make a new random id (hint: uuid.uuid4().hex).
      2. Store it in SESSIONS with a list holding just the system message.
      3. Return the id.
    """
    session_id = uuid.uuid4().hex
    SESSIONS[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return session_id


def end_session(session_id: str) -> None:
    """Forget a conversation.

    TODO: remove ``session_id`` from SESSIONS; raise UnknownSessionError if it isn't there.
    """
    if session_id not in SESSIONS:
        raise UnknownSessionError(session_id)
    del SESSIONS[session_id]


def trim_history(
    messages: list[dict[str, str]], max_turns: int = MAX_TURNS
) -> list[dict[str, str]]:
    """Keep the system message(s) plus only the last ``max_turns`` turns.

    A turn starts at a ``user`` message and includes the ``assistant`` reply after it.
    The newest user message (not answered yet) counts as a turn.

    TODO:
      1. Split the system messages from the rest.
      2. Find where each user message is. If there are more than max_turns, keep
         everything from the max_turns-th last user message onwards.
      3. Return system messages + the kept messages as a NEW list. Don't change
         ``messages`` itself: the caller may still be using it.
    """
    system_messages = [message for message in messages if message["role"] == "system"]
    conversation = [message for message in messages if message["role"] != "system"]
    user_positions = [
        index for index, message in enumerate(conversation) if message["role"] == "user"
    ]
    if len(user_positions) > max_turns:
        conversation = conversation[user_positions[-max_turns] :]
    return [*system_messages, *conversation]


def reply(session_id: str, text: str) -> str:
    """Answer ``text`` in this session and remember the turn.

    TODO:
      1. Check the message: strip it; raise ValueError if it's empty or longer than
         MAX_MESSAGE_CHARS.
      2. Get the session's history; raise UnknownSessionError if it doesn't exist.
      3. Build the messages to send: history + the new user message, trimmed.
      4. Call llm.chat(...). If the call fails (it raises llm.LLMError or openai.APIError),
         return FALLBACK_REPLY and save nothing, so the user can just try again.
      5. Save the trimmed history including the new user message and the reply.
      6. Return the reply.
    Never log or print ``text``: it may contain personal details.
    """
    clean = text.strip()
    if not clean:
        raise ValueError("Message must not be empty.")
    if len(clean) > MAX_MESSAGE_CHARS:
        raise ValueError(f"Message must be at most {MAX_MESSAGE_CHARS} characters.")
    if session_id not in SESSIONS:
        raise UnknownSessionError(session_id)

    messages = trim_history([*SESSIONS[session_id], {"role": "user", "content": clean}])
    try:
        answer = llm.chat(messages)
    except (llm.LLMError, openai.APIError):
        return FALLBACK_REPLY

    SESSIONS[session_id] = trim_history([*messages, {"role": "assistant", "content": answer}])
    return answer


def reply_stream(session_id: str, text: str) -> Iterator[str]:
    """Like :func:`reply`, but yields the answer piece by piece as the model writes it.

    TODO:
      1. Do the checks from reply() (steps 1-3) straight away, BEFORE streaming starts,
         so a bad message or unknown session raises when reply_stream() is called. Hint:
         make this a normal function that checks, then returns an inner generator.
         (A function with `yield` in it runs nothing until someone iterates it.)
      2. In the inner generator, loop over llm.chat_stream(messages), yield each piece
         and collect it.
      3. When the stream has finished, save the turn with the full reply ("".join(pieces)).
      4. If llm.LLMError or openai.APIError is raised, yield FALLBACK_REPLY and save
         nothing (not the question, not the half-written answer).
    """
    clean = text.strip()
    if not clean:
        raise ValueError("Message must not be empty.")
    if len(clean) > MAX_MESSAGE_CHARS:
        raise ValueError(f"Message must be at most {MAX_MESSAGE_CHARS} characters.")
    if session_id not in SESSIONS:
        raise UnknownSessionError(session_id)

    messages = trim_history([*SESSIONS[session_id], {"role": "user", "content": clean}])

    def pieces() -> Iterator[str]:
        collected: list[str] = []
        try:
            for piece in llm.chat_stream(messages):
                collected.append(piece)
                yield piece
        except (llm.LLMError, openai.APIError):
            yield FALLBACK_REPLY
            return

        answer = "".join(collected)
        SESSIONS[session_id] = trim_history([*messages, {"role": "assistant", "content": answer}])

    return pieces()
