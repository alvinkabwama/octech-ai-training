"""Domain errors raised by mini-EDRMS service functions.

The HTTP layer maps each one to a status code; service callers (including the
week 5 agent tools) can catch them directly.
"""


class DocumentNotFound(Exception):
    """No document exists with the requested id."""

    def __init__(self, doc_id: int) -> None:
        super().__init__(f"Document {doc_id} not found")
        self.doc_id = doc_id


class InvalidValue(ValueError):
    """A value is not one of the allowed choices."""

    def __init__(self, message: str, allowed: tuple[str, ...]) -> None:
        super().__init__(message)
        self.allowed = allowed


class OcrUnavailable(RuntimeError):
    """Text cannot be extracted: no Tesseract and no sidecar text file."""


class UploadRejected(ValueError):
    """An upload failed validation; ``status_code`` is the HTTP status to return."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code
