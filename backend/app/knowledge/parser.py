"""Document parsing: extract plain text from uploaded PDF/DOCX/TXT files."""

from pathlib import Path

from docx import Document
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {"pdf", "docx", "txt"}


class ParserError(Exception):
    """Raised when a document cannot be parsed into usable text."""


class UnsupportedFileTypeError(ParserError):
    def __init__(self, ext: str) -> None:
        super().__init__(f"Unsupported file type: .{ext}")
        self.ext = ext


def _parse_pdf(file_path: Path) -> str:
    try:
        reader = PdfReader(str(file_path))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:  # pragma: no cover - defensive, pypdf raises many types
        raise ParserError(f"Failed to parse PDF: {exc}") from exc
    return "\n\n".join(p.strip() for p in pages if p.strip())


def _parse_docx(file_path: Path) -> str:
    try:
        doc = Document(str(file_path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    except Exception as exc:  # pragma: no cover - defensive
        raise ParserError(f"Failed to parse DOCX: {exc}") from exc
    return "\n".join(paragraphs)


def _parse_txt(file_path: Path) -> str:
    raw = file_path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gb18030"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def parse_document(file_path: Path, filename: str) -> str:
    """Parse a document on disk into plain text, dispatching by file extension."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext == "pdf":
        text = _parse_pdf(file_path)
    elif ext == "docx":
        text = _parse_docx(file_path)
    elif ext == "txt":
        text = _parse_txt(file_path)
    else:
        raise UnsupportedFileTypeError(ext)

    if not text.strip():
        raise ParserError(
            "No extractable text found in document (it may be a scanned image "
            "without OCR, or an empty file)."
        )
    return text
