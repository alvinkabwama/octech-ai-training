"""Tests for document upload, storage, lookup and search."""

import sqlite3
from pathlib import Path

import pytest

from mini_edrms.app import audit, documents
from mini_edrms.app.errors import DocumentNotFound, UploadRejected


def test_create_and_get_document(conn: sqlite3.Connection, storage: Path) -> None:
    created = documents.create_document(conn, "memo.txt", b"Budget memo", storage)

    fetched = documents.get_document(conn, created.id)

    assert fetched == created
    assert fetched.filename == "memo.txt"
    assert fetched.status == "uploaded"
    assert fetched.category is None and fetched.department is None
    assert Path(fetched.stored_path).read_bytes() == b"Budget memo"


def test_create_records_audit(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "memo.txt", b"hello", storage)

    rows = audit.list_audit(conn, doc.id)

    assert len(rows) == 1
    assert rows[0]["action"] == "upload"
    assert rows[0]["actor"] == "user"
    assert rows[0]["doc_id"] == doc.id


def test_get_missing_raises(conn: sqlite3.Connection) -> None:
    with pytest.raises(DocumentNotFound):
        documents.get_document(conn, 999)


@pytest.mark.parametrize("name", ["../../evil.png", r"..\..\evil.png", "/etc/x/evil.png"])
def test_filename_path_parts_stripped(conn: sqlite3.Connection, storage: Path, name: str) -> None:
    doc = documents.create_document(conn, name, b"\x89PNG fake", storage)

    stored = Path(doc.stored_path)
    assert stored.name == f"{doc.id}_evil.png"
    assert stored.resolve().parent == storage.resolve()
    assert doc.filename == "evil.png"


def test_empty_upload_rejected(conn: sqlite3.Connection, storage: Path) -> None:
    with pytest.raises(UploadRejected) as exc:
        documents.create_document(conn, "empty.txt", b"", storage)
    assert exc.value.status_code == 400
    assert documents.list_documents(conn) == []


def test_oversize_rejected(conn: sqlite3.Connection, storage: Path) -> None:
    with pytest.raises(UploadRejected) as exc:
        documents.create_document(conn, "big.txt", b"x" * (10 * 1024 * 1024 + 1), storage)
    assert exc.value.status_code == 413


def test_exactly_max_size_accepted(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "max.txt", b"x" * (10 * 1024 * 1024), storage)
    assert doc.id > 0


@pytest.mark.parametrize("name", ["a.exe", "noextension", "..", "photo.png.exe"])
def test_bad_extension_rejected(conn: sqlite3.Connection, storage: Path, name: str) -> None:
    with pytest.raises(UploadRejected) as exc:
        documents.create_document(conn, name, b"data", storage)
    assert exc.value.status_code == 415
    assert list(storage.iterdir()) == []


def test_uppercase_extension_accepted(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "SCAN.PNG", b"img", storage)
    assert doc.filename == "SCAN.PNG"


def test_list_documents_returns_all(conn: sqlite3.Connection, storage: Path) -> None:
    first = documents.create_document(conn, "a.txt", b"one", storage)
    second = documents.create_document(conn, "b.txt", b"two", storage)

    assert [d.id for d in documents.list_documents(conn)] == [first.id, second.id]


def test_search_matches_text(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "letter.txt", b"x", storage)
    documents.create_document(conn, "other.txt", b"y", storage)
    conn.execute("UPDATE documents SET text = ? WHERE id = ?", ("Invoice for STATIONERY", doc.id))

    results = documents.search_documents(conn, "stationery")

    assert [d.id for d in results] == [doc.id]


def test_search_matches_filename(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "Contract_Lease.txt", b"x", storage)

    assert [d.id for d in documents.search_documents(conn, "lease")] == [doc.id]


def test_search_treats_wildcards_literally(conn: sqlite3.Connection, storage: Path) -> None:
    documents.create_document(conn, "a.txt", b"x", storage)

    assert documents.search_documents(conn, "%") == []
