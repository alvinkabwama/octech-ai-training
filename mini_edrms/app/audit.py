"""Audit log: every write records who did it (``user`` or ``agent``) and why."""

import sqlite3
from datetime import datetime, timezone
from typing import Any

from mini_edrms.app.errors import InvalidValue

ACTORS: tuple[str, ...] = ("user", "agent")


def validate_actor(actor: str) -> None:
    """Raise InvalidValue unless ``actor`` is one of ACTORS."""
    if actor not in ACTORS:
        raise InvalidValue(f"Unknown actor {actor!r}", ACTORS)


def record(
    conn: sqlite3.Connection,
    doc_id: int | None,
    action: str,
    actor: str,
    detail: str = "",
) -> None:
    """Append one audit row and commit.

    Args:
        conn: Open database connection.
        doc_id: Document the action applies to, or None for system-wide actions.
        action: Short verb, e.g. ``upload``, ``ocr``, ``file``, ``route``.
        actor: ``user`` or ``agent``.
        detail: Free text, typically the reason given for the change.

    Raises:
        InvalidValue: If ``actor`` is not ``user`` or ``agent``.
    """
    validate_actor(actor)
    ts = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "INSERT INTO audit (ts, doc_id, action, actor, detail) VALUES (?, ?, ?, ?, ?)",
        (ts, doc_id, action, actor, detail),
    )
    conn.commit()


def list_audit(conn: sqlite3.Connection, doc_id: int | None = None) -> list[dict[str, Any]]:
    """Return audit rows newest first, optionally only those for ``doc_id``."""
    if doc_id is None:
        rows = conn.execute("SELECT * FROM audit ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM audit WHERE doc_id = ? ORDER BY id DESC", (doc_id,)
        ).fetchall()
    return [dict(row) for row in rows]
