"""Week 2: put your chatbot behind an HTTP API with FastAPI.

Run it (from the repo root):

    .venv/bin/python -m uvicorn api:app --app-dir exercises/week-2-chatbot/starter --reload
    # PowerShell:
    .venv\\Scripts\\python -m uvicorn api:app --app-dir exercises\\week-2-chatbot\\starter --reload

then open http://127.0.0.1:8000/docs. The routes are thin: all the logic is in chatbot.py.

Routes use plain `def`, not `async def`: llm.chat blocks while it waits for the model, and
FastAPI runs plain `def` routes in a thread pool so one slow reply can't freeze the server.
"""

from __future__ import annotations

import chatbot  # noqa: F401  (your chatbot.py, next to this file)
from fastapi import FastAPI, HTTPException, Response  # noqa: F401  (you'll use these)
from fastapi.responses import StreamingResponse  # noqa: F401
from pydantic import BaseModel, ConfigDict, Field  # noqa: F401

app = FastAPI(title="Octech Help chatbot (week 2)")


class ChatRequest(BaseModel):
    """Body of POST /chat and POST /chat/stream.

    TODO:
      1. Reject unknown fields and strip spaces before checking the length:
         model_config = ConfigDict(extra="forbid", str_strip_whitespace=True).
         (Then "   " fails here, before a session is created for it.)
      2. session_id: optional string (None starts a new session).
      3. message: string, 1 to chatbot.MAX_MESSAGE_CHARS characters (use Field(...)).
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    session_id: str | None = None
    message: str = Field(min_length=1, max_length=chatbot.MAX_MESSAGE_CHARS)


class ChatResponse(BaseModel):
    """Body returned by POST /chat."""

    session_id: str
    reply: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    """Answer one message.

    TODO:
      1. Use request.session_id, or chatbot.new_session() if it's None.
      2. Call chatbot.reply(...).
      3. Turn chatbot.UnknownSessionError into HTTP 404 and ValueError into HTTP 422
         (raise HTTPException(status_code=..., detail=...)).
    """
    session_id = request.session_id if request.session_id is not None else chatbot.new_session()
    try:
        answer = chatbot.reply(session_id, request.message)
    except chatbot.UnknownSessionError as error:
        raise HTTPException(status_code=404, detail="Unknown session") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return ChatResponse(session_id=session_id, reply=answer)
    raise NotImplementedError("TODO: POST /chat")


@app.post("/chat/stream")
def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Answer one message as a stream of plain text.

    TODO:
      1. Same session handling and errors as chat(). chatbot.reply_stream() raises
         before streaming starts, so the 404/422 can still be sent.
      2. Return StreamingResponse(pieces, media_type="text/plain") with the session id
         in an "X-Session-Id" header (headers={...}), so the client can continue.
    """

    session_id = request.session_id if request.session_id is not None else chatbot.new_session()
    try:
        pieces = chatbot.reply_stream(session_id, request.message)
    except chatbot.UnknownSessionError as error:
        raise HTTPException(status_code=404, detail="Unknown session") from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return StreamingResponse(
        pieces,
        media_type="text/plain",
        headers={"X-Session-Id": session_id},
    )
    raise NotImplementedError("TODO: POST /chat/stream")


@app.delete("/chat/{session_id}", status_code=204)
def delete_chat(session_id: str) -> Response:
    """End a session.

    TODO: call chatbot.end_session(...); 404 if the session is unknown; then
    return Response(status_code=204).
    """
    try:
        chatbot.end_session(session_id)
    except chatbot.UnknownSessionError as error:
        raise HTTPException(status_code=404, detail="Unknown session") from error
    return Response(status_code=204)
    raise NotImplementedError("TODO: DELETE /chat/{session_id}")
