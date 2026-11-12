"""Test doubles for the OpenRouter helper. Used only by tests; never calls the network.

``FakeClient`` stands in for ``openai.OpenAI``: each ``chat.completions.create`` call is
recorded in ``calls`` and answered with the next scripted reply. A reply that is an
exception instance is raised instead, which is how tests simulate a 429.
"""

from __future__ import annotations

from collections.abc import Iterable
from types import SimpleNamespace
from typing import Any

import httpx
import openai

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def rate_limit_error() -> openai.RateLimitError:
    """A RateLimitError like the one the SDK raises on HTTP 429."""
    request = httpx.Request("POST", OPENROUTER_URL)
    response = httpx.Response(429, request=request)
    return openai.RateLimitError("Rate limit exceeded", response=response, body=None)


class _Completions:
    def __init__(self, owner: FakeClient) -> None:
        self._owner = owner

    def create(self, **kwargs: Any) -> SimpleNamespace:
        self._owner.calls.append(kwargs)
        if not self._owner.replies:
            raise AssertionError(
                f"Unexpected model call #{len(self._owner.calls)}: no scripted reply left"
            )
        reply = self._owner.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        message = SimpleNamespace(content=reply, role="assistant")
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message)], model=kwargs.get("model")
        )


class FakeClient:
    """Scripted stand-in for ``openai.OpenAI`` (only ``chat.completions.create``)."""

    def __init__(self, replies: Iterable[str | None | BaseException] = ()) -> None:
        self.replies: list[str | None | BaseException] = list(replies)
        self.calls: list[dict[str, Any]] = []
        self.chat = SimpleNamespace(completions=_Completions(self))

    def queue(self, *replies: str | None | BaseException) -> None:
        """Add replies for the next calls, in order."""
        self.replies.extend(replies)

    @property
    def last_messages(self) -> list[dict[str, str]]:
        """The ``messages`` sent with the most recent call."""
        if not self.calls:
            raise AssertionError("The model was never called")
        messages: list[dict[str, str]] = self.calls[-1]["messages"]
        return messages
