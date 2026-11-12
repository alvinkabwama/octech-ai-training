"""HTTP API tests: thin routes over the service functions."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mini_edrms.app.filing import CATEGORIES
from mini_edrms.app.main import create_app
from mini_edrms.app.routing import DEPARTMENTS


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with TestClient(create_app(tmp_path)) as test_client:
        yield test_client


def _upload(client: TestClient, name: str, content: bytes) -> dict:
    response = client.post("/documents", files={"file": (name, content, "text/plain")})
    assert response.status_code == 201, response.text
    return response.json()


def test_full_flow(client: TestClient) -> None:
    doc = _upload(client, "invoice.txt", b"Invoice 77 for printer toner")
    doc_id = doc["id"]
    assert doc["status"] == "uploaded"
    assert "stored_path" not in doc

    ocr = client.post(f"/documents/{doc_id}/ocr")
    assert ocr.status_code == 200
    assert ocr.json()["text"] == "Invoice 77 for printer toner"

    filed = client.put(
        f"/documents/{doc_id}/category", json={"category": "finance", "reason": "An invoice"}
    )
    assert filed.status_code == 200
    assert filed.json()["category"] == "finance"

    routed = client.post(
        f"/documents/{doc_id}/route", json={"department": "finance", "reason": "Pay it"}
    )
    assert routed.status_code == 200
    assert routed.json()["status"] == "routed"

    rows = client.get("/audit", params={"doc_id": doc_id}).json()
    assert [r["action"] for r in rows] == ["route", "file", "ocr", "upload"]
    assert all(r["actor"] == "user" for r in rows)

    assert client.get(f"/documents/{doc_id}").json()["department"] == "finance"
    assert [d["id"] for d in client.get("/documents").json()] == [doc_id]
    assert [d["id"] for d in client.get("/documents", params={"q": "toner"}).json()] == [doc_id]
    assert client.get("/documents", params={"q": "nothing-matches"}).json() == []


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("get", "/documents/999", None),
        ("post", "/documents/999/ocr", None),
        ("put", "/documents/999/category", {"category": "hr"}),
        ("post", "/documents/999/route", {"department": "registry"}),
    ],
)
def test_404_json(client: TestClient, method: str, path: str, body: dict | None) -> None:
    response = client.request(method, path, json=body)

    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert "999" in response.json()["detail"]


def test_invalid_category_422_lists_allowed(client: TestClient) -> None:
    doc_id = _upload(client, "a.txt", b"x")["id"]

    response = client.put(f"/documents/{doc_id}/category", json={"category": "sport"})

    assert response.status_code == 422
    assert response.json()["allowed"] == list(CATEGORIES)
    assert "sport" in response.json()["detail"]


def test_invalid_department_422_lists_allowed(client: TestClient) -> None:
    doc_id = _upload(client, "a.txt", b"x")["id"]

    response = client.post(f"/documents/{doc_id}/route", json={"department": "it"})

    assert response.status_code == 422
    assert response.json()["allowed"] == list(DEPARTMENTS)


def test_invalid_actor_422_lists_allowed(client: TestClient) -> None:
    doc_id = _upload(client, "a.txt", b"x")["id"]

    response = client.put(
        f"/documents/{doc_id}/category", json={"category": "hr", "actor": "robot"}
    )

    assert response.status_code == 422
    assert response.json()["allowed"] == ["user", "agent"]


def test_agent_actor_recorded(client: TestClient) -> None:
    doc_id = _upload(client, "a.txt", b"x")["id"]

    client.post(f"/documents/{doc_id}/route", json={"department": "legal", "actor": "agent"})

    assert client.get("/audit").json()[0]["actor"] == "agent"


@pytest.mark.parametrize(
    ("name", "content", "status"),
    [
        ("empty.txt", b"", 400),
        ("tool.exe", b"MZ", 415),
        ("big.txt", b"x" * (10 * 1024 * 1024 + 1), 413),
    ],
)
def test_upload_rejections(client: TestClient, name: str, content: bytes, status: int) -> None:
    response = client.post("/documents", files={"file": (name, content)})

    assert response.status_code == status
    assert response.json()["detail"]
    assert client.get("/documents").json() == []


def test_upload_path_traversal_stored_safely(client: TestClient, tmp_path: Path) -> None:
    doc = _upload(client, "../../evil.txt", b"x")

    assert doc["filename"] == "evil.txt"
    assert (tmp_path / "uploads" / f"{doc['id']}_evil.txt").is_file()
    assert not (tmp_path.parent / "evil.txt").exists()


def test_unknown_body_field_422(client: TestClient) -> None:
    doc_id = _upload(client, "a.txt", b"x")["id"]

    response = client.put(
        f"/documents/{doc_id}/category", json={"category": "hr", "priority": "high"}
    )

    assert response.status_code == 422


def test_ocr_unavailable_503(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda _name: None)
    doc_id = _upload(client, "no_sidecar_anywhere.png", b"\x89PNG fake")["id"]

    response = client.post(f"/documents/{doc_id}/ocr")

    assert response.status_code == 503
    assert "tesseract" in response.json()["detail"].lower()


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_create_app_does_not_touch_disk_until_startup(tmp_path: Path) -> None:
    data_dir = tmp_path / "later"

    app = create_app(data_dir)
    assert not data_dir.exists()

    with TestClient(app):
        assert (data_dir / "mini_edrms.db").is_file()
        assert (data_dir / "uploads").is_dir()


def test_data_dir_from_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINI_EDRMS_DATA_DIR", str(tmp_path / "env-data"))

    with TestClient(create_app()) as env_client:
        env_client.get("/health")

    assert (tmp_path / "env-data" / "mini_edrms.db").is_file()
