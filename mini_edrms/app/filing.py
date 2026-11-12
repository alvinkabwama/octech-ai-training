"""Filing: place a document under one category of the file plan."""

import sqlite3

from mini_edrms.app import audit, documents
from mini_edrms.app.documents import Document
from mini_edrms.app.errors import InvalidValue

CATEGORIES: tuple[str, ...] = ("correspondence", "hr", "finance", "procurement", "legal")


def set_category(
    conn: sqlite3.Connection,
    doc_id: int,
    category: str,
    actor: str = "user",
    reason: str = "",
) -> Document:
    """File a document under ``category``, set status ``filed`` and audit ``file``.

    Args:
        conn: Open database connection.
        doc_id: Document to file.
        category: One of CATEGORIES.
        actor: ``user`` or ``agent``.
        reason: Why this category was chosen; stored in the audit log.

    Raises:
        InvalidValue: If ``category`` or ``actor`` is not allowed.
        DocumentNotFound: If the document does not exist.
    """
    if category not in CATEGORIES:
        raise InvalidValue(
            f"Unknown category {category!r}; allowed: {', '.join(CATEGORIES)}", CATEGORIES
        )
    audit.validate_actor(actor)
    doc = documents.get_document(conn, doc_id)
    status = documents.advance_status(doc.status, "filed")
    conn.execute(
        "UPDATE documents SET category = ?, status = ? WHERE id = ?", (category, status, doc_id)
    )
    audit.record(conn, doc_id, "file", actor, f"category={category}; reason={reason}")
    return documents.get_document(conn, doc_id)
