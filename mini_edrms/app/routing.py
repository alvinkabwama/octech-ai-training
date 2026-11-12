"""Routing: send a document to the department that should act on it."""

import sqlite3

from mini_edrms.app import audit, documents
from mini_edrms.app.documents import Document
from mini_edrms.app.errors import InvalidValue

DEPARTMENTS: tuple[str, ...] = (
    "registry",
    "human_resources",
    "finance",
    "procurement",
    "legal",
    "director",
)


def route_document(
    conn: sqlite3.Connection,
    doc_id: int,
    department: str,
    actor: str = "user",
    reason: str = "",
) -> Document:
    """Route a document to ``department``, set status ``routed`` and audit ``route``.

    Args:
        conn: Open database connection.
        doc_id: Document to route.
        department: One of DEPARTMENTS.
        actor: ``user`` or ``agent``.
        reason: Why this department was chosen; stored in the audit log.

    Raises:
        InvalidValue: If ``department`` or ``actor`` is not allowed.
        DocumentNotFound: If the document does not exist.
    """
    if department not in DEPARTMENTS:
        raise InvalidValue(
            f"Unknown department {department!r}; allowed: {', '.join(DEPARTMENTS)}", DEPARTMENTS
        )
    audit.validate_actor(actor)
    doc = documents.get_document(conn, doc_id)
    status = documents.advance_status(doc.status, "routed")
    conn.execute(
        "UPDATE documents SET department = ?, status = ? WHERE id = ?",
        (department, status, doc_id),
    )
    audit.record(conn, doc_id, "route", actor, f"department={department}; reason={reason}")
    return documents.get_document(conn, doc_id)
