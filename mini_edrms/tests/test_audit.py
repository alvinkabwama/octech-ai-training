"""Tests for the audit log."""

import sqlite3

import pytest

from mini_edrms.app import audit
from mini_edrms.app.errors import InvalidValue


def test_record_and_list_newest_first(conn: sqlite3.Connection) -> None:
    audit.record(conn, None, "first", "user")
    audit.record(conn, None, "second", "agent", "because")

    rows = audit.list_audit(conn)

    assert [r["action"] for r in rows] == ["second", "first"]
    assert rows[0]["actor"] == "agent"
    assert rows[0]["detail"] == "because"
    assert rows[0]["ts"]


def test_list_audit_filters_by_doc(conn: sqlite3.Connection) -> None:
    audit.record(conn, 1, "a", "user")
    audit.record(conn, 2, "b", "user")

    assert [r["action"] for r in audit.list_audit(conn, 2)] == ["b"]


def test_audit_rejects_unknown_actor(conn: sqlite3.Connection) -> None:
    with pytest.raises(InvalidValue) as exc:
        audit.record(conn, None, "upload", "robot")

    assert set(exc.value.allowed) == {"user", "agent"}
    assert audit.list_audit(conn) == []
