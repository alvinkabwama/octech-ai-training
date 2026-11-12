"""Shared fixtures for mini-EDRMS tests."""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest

from mini_edrms.app import db


@pytest.fixture
def conn() -> Iterator[sqlite3.Connection]:
    """An initialised in-memory database."""
    connection = db.connect(":memory:")
    db.init_db(connection)
    yield connection
    connection.close()


@pytest.fixture
def storage(tmp_path: Path) -> Path:
    """A per-test directory for stored upload files."""
    return tmp_path
