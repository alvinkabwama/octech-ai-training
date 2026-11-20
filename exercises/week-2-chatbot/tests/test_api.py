"""Week 2 checks for starter/api.py (the FastAPI front of your chatbot).

TestClient calls the app in-process, so no server is started and the model is faked.
"""

import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from fastapi.testclient import TestClient

from exercises.common.testing import FakeClient


@pytest.fixture
def client(
    load_starter: Callable[[str], ModuleType], monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    # api.py does `import chatbot`, as it would under `uvicorn --app-dir <starter folder>`.
    starter_dir = Path(str(load_starter("chatbot").__file__)).parent
    monkeypatch.syspath_prepend(str(starter_dir))
    monkeypatch.delitem(sys.modules, "chatbot", raising=False)
    api = load_starter("api")
    api.chatbot.SESSIONS.clear()
    return TestClient(api.app)


def test_chat_creates_session_then_remembers(client: TestClient, fake_llm: FakeClient) -> None:
    fake_llm.queue("Hi Amina.", "You are Amina.")

    first = client.post("/chat", json={"message": "I am Amina."})
    session_id = first.json()["session_id"]
    second = client.post("/chat", json={"session_id": session_id, "message": "Who am I?"})

    assert first.status_code == 200
    assert first.json() == {"session_id": session_id, "reply": "Hi Amina."}
    assert second.json() == {"session_id": session_id, "reply": "You are Amina."}
    assert {"role": "assistant", "content": "Hi Amina."} in fake_llm.last_messages


def test_unknown_session_is_404(client: TestClient, fake_llm: FakeClient) -> None:
    body = {"session_id": "no-such-session", "message": "Hi"}

    assert client.post("/chat", json=body).status_code == 404
    assert client.post("/chat/stream", json=body).status_code == 404
    assert client.delete("/chat/no-such-session").status_code == 404
    assert fake_llm.calls == []


@pytest.mark.parametrize(
    "body",
    [
        {"message": ""},
        {"message": "   "},
        {"message": "x" * 2001},
        {"message": "Hi", "unexpected": "field"},
        {},
    ],
)
def test_api_rejects_bad_body(
    client: TestClient, fake_llm: FakeClient, body: dict[str, Any]
) -> None:
    assert client.post("/chat", json=body).status_code == 422
    assert client.post("/chat/stream", json=body).status_code == 422
    assert fake_llm.calls == []


def test_stream_endpoint_streams_text_with_session_header(
    client: TestClient, fake_llm: FakeClient
) -> None:
    fake_llm.queue_stream(["Octech ", "Help ", "here."])

    response = client.post("/chat/stream", json={"message": "Hello"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert response.text == "Octech Help here."
    assert response.headers["x-session-id"]


def test_delete_ends_session(client: TestClient, fake_llm: FakeClient) -> None:
    fake_llm.queue("Hi.")
    session_id = client.post("/chat", json={"message": "Hi"}).json()["session_id"]

    assert client.delete(f"/chat/{session_id}").status_code == 204
    gone = client.post("/chat", json={"session_id": session_id, "message": "Hi"})
    assert gone.status_code == 404
