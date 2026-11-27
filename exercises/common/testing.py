"""Test doubles for the OpenRouter helper. Used only by tests; never calls the network.

``FakeClient`` stands in for ``openai.OpenAI``: each ``chat.completions.create`` call is
recorded in ``calls`` and answered with the next scripted reply. A reply that is an
exception instance is raised instead, which is how tests simulate a 429.

Streaming: ``queue_stream(["Hel", "lo"])`` scripts a reply for a ``stream=True`` call. It is
returned as chunks shaped like the SDK's ``ChatCompletionChunk`` (``choices[0].delta.content``),
followed by one chunk with no choices (OpenRouter's final usage chunk). Inside a pieces list,
``None`` is a chunk with no content, and an exception instance is raised mid-stream.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
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


def api_error(message: str = "Upstream provider error", code: int | None = None) -> openai.APIError:
    """A plain APIError, like the SDK raises for an error event inside a stream.

    OpenRouter reports failures after the HTTP 200 as ``{"error": {"code": ..., "message": ...}}``
    in the stream; the SDK turns that into ``openai.APIError`` with ``body`` set to the error.
    """
    request = httpx.Request("POST", OPENROUTER_URL)
    body = {"code": code, "message": message} if code is not None else None
    return openai.APIError(message, request, body=body)


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
        streaming = bool(kwargs.get("stream"))
        if isinstance(reply, _StreamScript):
            if not streaming:
                raise AssertionError("A streamed reply was queued, but the call lacks stream=True")
            return self._owner._new_stream(reply.pieces)
        if streaming:
            # A plain reply asked for as a stream arrives as one piece.
            return self._owner._new_stream([reply])
        message = SimpleNamespace(content=reply, role="assistant")
        return SimpleNamespace(
            choices=[SimpleNamespace(message=message)], model=kwargs.get("model")
        )


class _StreamScript:
    """Pieces queued with ``FakeClient.queue_stream``."""

    def __init__(self, pieces: Iterable[str | None | BaseException]) -> None:
        self.pieces = list(pieces)


def _chunk(content: str | None) -> SimpleNamespace:
    delta = SimpleNamespace(content=content, role="assistant")
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta, index=0)])


class _FakeStream:
    """Iterable of fake chunks, with ``close()`` like the SDK's ``Stream``."""

    def __init__(self, pieces: list[str | None | BaseException]) -> None:
        self._pieces = pieces
        self.closed = False

    def __iter__(self) -> Iterator[SimpleNamespace]:
        for piece in self._pieces:
            if isinstance(piece, BaseException):
                raise piece
            yield _chunk(piece)
        yield SimpleNamespace(choices=[])  # final usage-style chunk, no content

    def close(self) -> None:
        self.closed = True


class FakeClient:
    """Scripted stand-in for ``openai.OpenAI`` (only ``chat.completions.create``)."""

    def __init__(self, replies: Iterable[str | None | BaseException] = ()) -> None:
        self.replies: list[str | None | BaseException | _StreamScript] = list(replies)
        self.calls: list[dict[str, Any]] = []
        self.streams: list[_FakeStream] = []  # every stream handed out, to check .closed
        self.chat = SimpleNamespace(completions=_Completions(self))

    def queue(self, *replies: str | None | BaseException) -> None:
        """Add replies for the next calls, in order."""
        self.replies.extend(replies)

    def _new_stream(self, pieces: list[str | None | BaseException]) -> _FakeStream:
        stream = _FakeStream(pieces)
        self.streams.append(stream)
        return stream

    def queue_stream(self, *pieces_lists: Iterable[str | None | BaseException]) -> None:
        """Add streamed replies (one list of pieces per ``stream=True`` call), in order."""
        self.replies.extend(_StreamScript(pieces) for pieces in pieces_lists)

    @property
    def last_messages(self) -> list[dict[str, str]]:
        """The ``messages`` sent with the most recent call."""
        if not self.calls:
            raise AssertionError("The model was never called")
        messages: list[dict[str, str]] = self.calls[-1]["messages"]
        return messages
