"""SQLite connection and schema (stdlib sqlite3, no server)."""

import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    uploaded_at TEXT NOT NULL,
    text        TEXT,
    category    TEXT,
    department  TEXT,
    status      TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      TEXT NOT NULL,
    doc_id  INTEGER,
    action  TEXT NOT NULL,
    actor   TEXT NOT NULL,
    detail  TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_audit_doc_id ON audit (doc_id);
"""


def connect(path: Path | str) -> sqlite3.Connection:
    """Open a SQLite connection whose rows can be read by column name.

    Args:
        path: Database file path, or ``":memory:"`` for an in-memory database.
    """
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    return connection


def init_db(conn: sqlite3.Connection) -> None:
    """Create the ``documents`` and ``audit`` tables if they do not exist."""
    conn.executescript(SCHEMA)
    conn.commit()
