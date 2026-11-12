"""Text extraction: read .txt directly, OCR images with Tesseract, else use a sidecar .txt.

The sidecar fallback means Windows users without Tesseract are never blocked: each
sample image ships with ``<stem>.txt`` holding the same text.
"""

import shutil
import sqlite3
from pathlib import Path

from mini_edrms.app import audit, documents
from mini_edrms.app.errors import OcrUnavailable

DEFAULT_SAMPLES_DIR = Path(__file__).resolve().parents[1] / "samples"
INSTALL_HINT = (
    "Install Tesseract (Windows: https://github.com/UB-Mannheim/tesseract/wiki, "
    "macOS: brew install tesseract, Linux: apt install tesseract-ocr) "
    "or provide a sidecar .txt file."
)


def _tesseract_text(image_path: Path) -> str | None:
    """Return OCR text, or None if Tesseract is missing or cannot read the image."""
    if shutil.which("tesseract") is None:
        return None
    import pytesseract
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(image_path) as image:
            return str(pytesseract.image_to_string(image)).strip()
    except (OSError, UnidentifiedImageError, pytesseract.TesseractError):
        return None


def _sidecar_text(samples_dir: Path, filename: str) -> str | None:
    sidecar = samples_dir / f"{Path(filename).stem}.txt"
    if sidecar.is_file():
        return sidecar.read_text(encoding="utf-8").strip()
    return None


def extract_text(
    conn: sqlite3.Connection,
    doc_id: int,
    samples_dir: Path | None = None,
    actor: str = "user",
) -> str:
    """Extract and save a document's text, set status ``ocr_done`` and audit ``ocr``.

    Order: ``.txt`` files are read directly; images use Tesseract when it is on
    PATH; otherwise ``samples_dir/<original stem>.txt`` is used. A document already
    filed or routed keeps its status.

    Args:
        conn: Open database connection.
        doc_id: Document to process.
        samples_dir: Where sidecar files live; defaults to the bundled samples.
        actor: ``user`` or ``agent``.

    Raises:
        DocumentNotFound: If the document does not exist.
        OcrUnavailable: If no Tesseract and no sidecar file.
        InvalidValue: If ``actor`` is not ``user`` or ``agent``.
    """
    audit.validate_actor(actor)
    doc = documents.get_document(conn, doc_id)
    stored = Path(doc.stored_path)

    if stored.suffix.lower() == ".txt":
        text = stored.read_bytes().decode("utf-8", errors="replace").strip()
        method = "text file"
    else:
        text = _tesseract_text(stored)
        method = "tesseract"
        if text is None:
            text = _sidecar_text(samples_dir or DEFAULT_SAMPLES_DIR, doc.filename)
            method = "sidecar"
        if text is None:
            raise OcrUnavailable(f"Cannot extract text from {doc.filename}. {INSTALL_HINT}")

    status = "ocr_done" if doc.status == "uploaded" else doc.status
    conn.execute("UPDATE documents SET text = ?, status = ? WHERE id = ?", (text, status, doc_id))
    audit.record(conn, doc_id, "ocr", actor, f"Extracted {len(text)} chars via {method}")
    return text
