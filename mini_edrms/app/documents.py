"""Document upload, storage, lookup and search."""

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from mini_edrms.app import audit
from mini_edrms.app.errors import DocumentNotFound, UploadRejected

ALLOWED_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".txt")
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
STATUSES: tuple[str, ...] = ("uploaded", "ocr_done", "filed", "routed")

_LIKE_ESCAPE = "\\"


@dataclass(frozen=True)
class Document:
    """One stored document and its records-management metadata."""

    id: int
    filename: str
    stored_path: str
    uploaded_at: str
    text: str | None
    category: str | None
    department: str | None
    status: str


def advance_status(current: str, target: str) -> str:
    """Return the later of two statuses, so a status never moves backwards."""
    return max(current, target, key=STATUSES.index)


def _row_to_document(row: sqlite3.Row) -> Document:
    return Document(**{key: row[key] for key in row.keys()})


def safe_basename(filename: str) -> str:
    """Drop any directory parts (``/`` or ``\\``) so a name cannot escape storage."""
    return re.split(r"[\\/]", filename)[-1].strip()


def _validate_upload(name: str, content: bytes) -> None:
    if name.startswith(".") or Path(name).suffix.lower() not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(ALLOWED_EXTENSIONS)
        raise UploadRejected(f"Unsupported file type; allowed: {allowed}", 415)
    if not content:
        raise UploadRejected("File is empty", 400)
    if len(content) > MAX_UPLOAD_BYTES:
        raise UploadRejected(f"File exceeds {MAX_UPLOAD_BYTES} bytes", 413)


def create_document(
    conn: sqlite3.Connection,
    filename: str,
    content: bytes,
    storage_dir: Path,
    actor: str = "user",
) -> Document:
    """Store an uploaded file and create its document record (status ``uploaded``).

    The file is saved as ``<id>_<basename>`` inside ``storage_dir``; any directory
    parts in ``filename`` are discarded.

    Raises:
        UploadRejected: 415 for an unsupported extension, 400 for an empty file,
            413 for a file over 10 MB.
        InvalidValue: If ``actor`` is not ``user`` or ``agent``.
    """
    audit.validate_actor(actor)
    name = safe_basename(filename)
    _validate_upload(name, content)

    uploaded_at = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        "INSERT INTO documents (filename, stored_path, uploaded_at, status) VALUES (?, '', ?, ?)",
        (name, uploaded_at, "uploaded"),
    )
    doc_id = int(cursor.lastrowid or 0)
    stored = Path(storage_dir) / f"{doc_id}_{name}"
    try:
        stored.write_bytes(content)
    except OSError:
        conn.rollback()
        raise
    conn.execute("UPDATE documents SET stored_path = ? WHERE id = ?", (str(stored), doc_id))
    audit.record(conn, doc_id, "upload", actor, f"Uploaded {name}")
    return get_document(conn, doc_id)


def get_document(conn: sqlite3.Connection, doc_id: int) -> Document:
    """Return one document.

    Raises:
        DocumentNotFound: If no document has this id.
    """
    row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    if row is None:
        raise DocumentNotFound(doc_id)
    return _row_to_document(row)


def list_documents(conn: sqlite3.Connection) -> list[Document]:
    """Return all documents, oldest first."""
    rows = conn.execute("SELECT * FROM documents ORDER BY id").fetchall()
    return [_row_to_document(row) for row in rows]


def _escape_like(value: str) -> str:
    for char in (_LIKE_ESCAPE, "%", "_"):
        value = value.replace(char, _LIKE_ESCAPE + char)
    return value


def search_documents(conn: sqlite3.Connection, query: str) -> list[Document]:
    """Return documents whose filename or extracted text contains ``query``.

    Matching is case-insensitive (ASCII) and ``%``/``_`` are treated literally.
    """
    pattern = f"%{_escape_like(query)}%"
    rows = conn.execute(
        "SELECT * FROM documents WHERE filename LIKE :p ESCAPE :e OR text LIKE :p ESCAPE :e "
        "ORDER BY id",
        {"p": pattern, "e": _LIKE_ESCAPE},
    ).fetchall()
    return [_row_to_document(row) for row in rows]
