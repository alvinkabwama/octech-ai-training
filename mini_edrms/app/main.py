"""FastAPI app: thin HTTP wrappers over the mini-EDRMS service functions.

Run with ``make run`` (``uvicorn mini_edrms.app.main:app --reload``).
"""

import os
import sqlite3
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Request, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from mini_edrms.app import audit, db, documents, filing, ocr, routing
from mini_edrms.app.documents import MAX_UPLOAD_BYTES, Document
from mini_edrms.app.errors import DocumentNotFound, InvalidValue, OcrUnavailable, UploadRejected

DB_FILENAME = "mini_edrms.db"
UPLOADS_DIRNAME = "uploads"


class DocumentOut(BaseModel):
    """A document as returned over HTTP (the server-side storage path is not exposed)."""

    id: int
    filename: str
    uploaded_at: str
    text: str | None
    category: str | None
    department: str | None
    status: str

    @classmethod
    def from_document(cls, doc: Document) -> "DocumentOut":
        return cls(
            id=doc.id,
            filename=doc.filename,
            uploaded_at=doc.uploaded_at,
            text=doc.text,
            category=doc.category,
            department=doc.department,
            status=doc.status,
        )


class CategoryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str
    reason: str = ""
    actor: str = "user"


class RouteIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    department: str
    reason: str = ""
    actor: str = "user"


class AuditOut(BaseModel):
    id: int
    ts: str
    doc_id: int | None
    action: str
    actor: str
    detail: str


def _resolve_data_dir(data_dir: Path | None) -> Path:
    return Path(data_dir or os.environ.get("MINI_EDRMS_DATA_DIR") or "data")


def _register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DocumentNotFound)
    async def not_found(_request: Request, exc: DocumentNotFound) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(InvalidValue)
    async def invalid_value(_request: Request, exc: InvalidValue) -> JSONResponse:
        return JSONResponse(
            status_code=422, content={"detail": str(exc), "allowed": list(exc.allowed)}
        )

    @app.exception_handler(UploadRejected)
    async def upload_rejected(_request: Request, exc: UploadRejected) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})

    @app.exception_handler(OcrUnavailable)
    async def ocr_unavailable(_request: Request, exc: OcrUnavailable) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})


def create_app(data_dir: Path | None = None) -> FastAPI:
    """Build the API. Nothing touches disk until startup.

    Args:
        data_dir: Holds ``mini_edrms.db`` and ``uploads/``. Defaults to the
            ``MINI_EDRMS_DATA_DIR`` environment variable, else ``./data``.
    """
    root = _resolve_data_dir(data_dir)
    db_path = root / DB_FILENAME
    uploads_dir = root / UPLOADS_DIRNAME

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        uploads_dir.mkdir(parents=True, exist_ok=True)
        connection = db.connect(db_path)
        try:
            db.init_db(connection)
        finally:
            connection.close()
        yield

    app = FastAPI(title="mini-EDRMS", version="0.1.0", lifespan=lifespan)
    _register_error_handlers(app)

    def get_conn() -> Iterator[sqlite3.Connection]:
        connection = db.connect(db_path)
        try:
            yield connection
        finally:
            connection.close()

    Conn = Annotated[sqlite3.Connection, Depends(get_conn)]

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/documents", status_code=status.HTTP_201_CREATED, response_model=DocumentOut)
    def upload_document(file: UploadFile, conn: Conn) -> DocumentOut:
        content = file.file.read(MAX_UPLOAD_BYTES + 1)
        doc = documents.create_document(conn, file.filename or "", content, uploads_dir)
        return DocumentOut.from_document(doc)

    @app.get("/documents", response_model=list[DocumentOut])
    def list_documents(conn: Conn, q: str | None = None) -> list[DocumentOut]:
        found = documents.search_documents(conn, q) if q else documents.list_documents(conn)
        return [DocumentOut.from_document(doc) for doc in found]

    @app.get("/documents/{doc_id}", response_model=DocumentOut)
    def get_document(doc_id: int, conn: Conn) -> DocumentOut:
        return DocumentOut.from_document(documents.get_document(conn, doc_id))

    @app.post("/documents/{doc_id}/ocr", response_model=DocumentOut)
    def run_ocr(doc_id: int, conn: Conn) -> DocumentOut:
        ocr.extract_text(conn, doc_id)
        return DocumentOut.from_document(documents.get_document(conn, doc_id))

    @app.put("/documents/{doc_id}/category", response_model=DocumentOut)
    def set_category(doc_id: int, body: CategoryIn, conn: Conn) -> DocumentOut:
        doc = filing.set_category(conn, doc_id, body.category, body.actor, body.reason)
        return DocumentOut.from_document(doc)

    @app.post("/documents/{doc_id}/route", response_model=DocumentOut)
    def route_document(doc_id: int, body: RouteIn, conn: Conn) -> DocumentOut:
        doc = routing.route_document(conn, doc_id, body.department, body.actor, body.reason)
        return DocumentOut.from_document(doc)

    @app.get("/audit", response_model=list[AuditOut])
    def list_audit(conn: Conn, doc_id: int | None = None) -> list[dict[str, Any]]:
        return audit.list_audit(conn, doc_id)

    return app


app = create_app()
