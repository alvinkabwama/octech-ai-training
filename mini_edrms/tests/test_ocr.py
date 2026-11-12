"""Tests for text extraction (Tesseract with sidecar .txt fallback)."""

import shutil
import sqlite3
from io import BytesIO
from pathlib import Path

import pytest

from mini_edrms.app import audit, documents, ocr
from mini_edrms.app.errors import DocumentNotFound, OcrUnavailable

HAS_TESSERACT = shutil.which("tesseract") is not None


@pytest.fixture
def samples(tmp_path: Path) -> Path:
    directory = tmp_path / "samples"
    directory.mkdir()
    return directory


@pytest.fixture
def no_tesseract(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "which", lambda _name: None)


def test_txt_document_text_extracted(
    conn: sqlite3.Connection, storage: Path, samples: Path
) -> None:
    doc = documents.create_document(conn, "memo.txt", b"Please approve the budget.", storage)

    text = ocr.extract_text(conn, doc.id, samples)

    assert text == "Please approve the budget."
    assert documents.get_document(conn, doc.id).text == text


def test_image_uses_sidecar_when_no_tesseract(
    conn: sqlite3.Connection, storage: Path, samples: Path, no_tesseract: None
) -> None:
    (samples / "invoice_01.txt").write_text("Invoice 001 for office chairs", encoding="utf-8")
    doc = documents.create_document(conn, "invoice_01.png", b"\x89PNG not real", storage)

    assert ocr.extract_text(conn, doc.id, samples) == "Invoice 001 for office chairs"


def test_no_tesseract_no_sidecar_raises(
    conn: sqlite3.Connection, storage: Path, samples: Path, no_tesseract: None
) -> None:
    doc = documents.create_document(conn, "scan.jpg", b"jpeg bytes", storage)

    with pytest.raises(OcrUnavailable, match="(?i)install tesseract"):
        ocr.extract_text(conn, doc.id, samples)

    unchanged = documents.get_document(conn, doc.id)
    assert unchanged.status == "uploaded" and unchanged.text is None
    assert [r["action"] for r in audit.list_audit(conn, doc.id)] == ["upload"]


def test_ocr_sets_status_and_audits(conn: sqlite3.Connection, storage: Path, samples: Path) -> None:
    doc = documents.create_document(conn, "memo.txt", b"hello", storage)

    ocr.extract_text(conn, doc.id, samples, actor="agent")

    assert documents.get_document(conn, doc.id).status == "ocr_done"
    latest = audit.list_audit(conn, doc.id)[0]
    assert latest["action"] == "ocr"
    assert latest["actor"] == "agent"


def test_reocr_keeps_later_status(conn: sqlite3.Connection, storage: Path, samples: Path) -> None:
    doc = documents.create_document(conn, "memo.txt", b"hello", storage)
    conn.execute("UPDATE documents SET status = 'routed' WHERE id = ?", (doc.id,))

    ocr.extract_text(conn, doc.id, samples)

    assert documents.get_document(conn, doc.id).status == "routed"


def test_missing_document_raises(conn: sqlite3.Connection, samples: Path) -> None:
    with pytest.raises(DocumentNotFound):
        ocr.extract_text(conn, 404, samples)


def test_default_samples_dir_is_bundled_samples() -> None:
    assert ocr.DEFAULT_SAMPLES_DIR == Path(ocr.__file__).resolve().parents[1] / "samples"


def test_tesseract_failure_falls_back_to_sidecar(
    conn: sqlite3.Connection,
    storage: Path,
    samples: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(shutil, "which", lambda _name: "/fake/tesseract")
    (samples / "broken.txt").write_text("sidecar text", encoding="utf-8")
    doc = documents.create_document(conn, "broken.png", b"not an image", storage)

    assert ocr.extract_text(conn, doc.id, samples) == "sidecar text"


@pytest.mark.skipif(not HAS_TESSERACT, reason="Tesseract is not installed")
def test_tesseract_reads_sample_image(
    conn: sqlite3.Connection, storage: Path, samples: Path
) -> None:
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (1200, 200), "white")
    font = ImageFont.load_default(size=48)
    ImageDraw.Draw(image).text((40, 60), "PROCUREMENT REQUEST", fill="black", font=font)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    doc = documents.create_document(conn, "generated.png", buffer.getvalue(), storage)

    text = ocr.extract_text(conn, doc.id, samples)

    assert "PROCUREMENT" in text.upper()
