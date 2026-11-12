"""Tests for filing a document under a file-plan category."""

import sqlite3
from pathlib import Path

import pytest

from mini_edrms.app import audit, documents, filing
from mini_edrms.app.errors import DocumentNotFound, InvalidValue


def test_categories_are_the_file_plan() -> None:
    assert filing.CATEGORIES == ("correspondence", "hr", "finance", "procurement", "legal")


def test_set_category_files_document(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "a.txt", b"x", storage)

    filed = filing.set_category(conn, doc.id, "finance")

    assert filed.category == "finance"
    assert filed.status == "filed"
    assert documents.get_document(conn, doc.id) == filed


def test_invalid_category_lists_allowed(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "a.txt", b"x", storage)

    with pytest.raises(InvalidValue) as exc:
        filing.set_category(conn, doc.id, "Finance")

    assert exc.value.allowed == filing.CATEGORIES
    assert "finance" in str(exc.value)
    assert documents.get_document(conn, doc.id).category is None


def test_set_category_missing_doc_raises(conn: sqlite3.Connection) -> None:
    with pytest.raises(DocumentNotFound):
        filing.set_category(conn, 42, "hr")


def test_set_category_audits_actor_and_reason(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "a.txt", b"x", storage)

    filing.set_category(conn, doc.id, "legal", actor="agent", reason="Mentions a lease")

    row = audit.list_audit(conn, doc.id)[0]
    assert row["action"] == "file"
    assert row["actor"] == "agent"
    assert "Mentions a lease" in row["detail"]
    assert "legal" in row["detail"]


def test_set_category_rejects_unknown_actor(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "a.txt", b"x", storage)

    with pytest.raises(InvalidValue):
        filing.set_category(conn, doc.id, "hr", actor="bot")

    assert documents.get_document(conn, doc.id).category is None


def test_refiling_routed_document_keeps_routed(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "a.txt", b"x", storage)
    conn.execute("UPDATE documents SET status = 'routed' WHERE id = ?", (doc.id,))

    assert filing.set_category(conn, doc.id, "hr").status == "routed"
