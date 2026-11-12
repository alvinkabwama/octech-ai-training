"""Tests for routing a document to a department."""

import sqlite3
from pathlib import Path

import pytest

from mini_edrms.app import audit, documents, routing
from mini_edrms.app.errors import DocumentNotFound, InvalidValue


def test_departments_list() -> None:
    assert routing.DEPARTMENTS == (
        "registry",
        "human_resources",
        "finance",
        "procurement",
        "legal",
        "director",
    )


def test_route_document_sets_department(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "a.txt", b"x", storage)

    routed = routing.route_document(conn, doc.id, "human_resources")

    assert routed.department == "human_resources"
    assert routed.status == "routed"
    assert documents.get_document(conn, doc.id) == routed


def test_invalid_department_lists_allowed(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "a.txt", b"x", storage)

    with pytest.raises(InvalidValue) as exc:
        routing.route_document(conn, doc.id, "hr")

    assert exc.value.allowed == routing.DEPARTMENTS
    assert "human_resources" in str(exc.value)
    assert documents.get_document(conn, doc.id).department is None


def test_route_missing_doc_raises(conn: sqlite3.Connection) -> None:
    with pytest.raises(DocumentNotFound):
        routing.route_document(conn, 42, "registry")


def test_route_audits_actor_and_reason(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "a.txt", b"x", storage)

    routing.route_document(conn, doc.id, "director", actor="agent", reason="Board matter")

    row = audit.list_audit(conn, doc.id)[0]
    assert row["action"] == "route"
    assert row["actor"] == "agent"
    assert "Board matter" in row["detail"]
    assert "director" in row["detail"]


def test_route_rejects_unknown_actor(conn: sqlite3.Connection, storage: Path) -> None:
    doc = documents.create_document(conn, "a.txt", b"x", storage)

    with pytest.raises(InvalidValue):
        routing.route_document(conn, doc.id, "registry", actor="")

    assert documents.get_document(conn, doc.id).department is None
