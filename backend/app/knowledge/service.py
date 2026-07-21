"""Document lifecycle orchestration: upload, replace, delete.

Each operation keeps `knowledge_chunks` (ORM) and `vec_chunks` (sqlite-vec
virtual table) consistent by writing both through the same SQLAlchemy Session
inside a single transaction, per the design in the approved plan.
"""

import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.knowledge.chunker import chunk_text
from app.knowledge.embedding import embed_texts
from app.knowledge.parser import ParserError, parse_document
from app.knowledge.store import delete_vectors_for_document, insert_vectors
from app.models import KnowledgeChunk, KnowledgeDocument

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


class UnsupportedFileTypeError(Exception):
    pass


class FileTooLargeError(Exception):
    pass


def _storage_dir() -> Path:
    directory = Path(settings.knowledge_storage_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _validate_upload(filename: str, size_bytes: int) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileTypeError(f"Unsupported file type: .{ext}")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if size_bytes > max_bytes:
        raise FileTooLargeError(
            f"File exceeds the {settings.max_upload_mb}MB upload limit."
        )
    return ext


def _save_upload_to_disk(content: bytes, ext: str) -> Path:
    filename = f"{uuid.uuid4().hex}.{ext}"
    path = _storage_dir() / filename
    path.write_bytes(content)
    return path


def _build_chunks_and_vectors(
    text: str,
) -> tuple[list[str], list[list[float]]]:
    """Chunk text and embed each chunk. Raises ParserError if chunking yields
    nothing usable."""
    chunks = chunk_text(text)
    if not chunks:
        raise ParserError("Document produced no usable text chunks.")
    vectors = embed_texts(chunks)
    return chunks, vectors


def _insert_chunks_and_vectors(
    db: Session, document_id: int, chunks: list[str], vectors: list[list[float]]
) -> int:
    chunk_rows = [
        KnowledgeChunk(document_id=document_id, chunk_index=idx, text=chunk_text_)
        for idx, chunk_text_ in enumerate(chunks)
    ]
    db.add_all(chunk_rows)
    db.flush()  # assign ids, used as vec_chunks.chunk_id
    chunk_ids = [row.id for row in chunk_rows]
    insert_vectors(db, chunk_ids, vectors)
    return len(chunk_rows)


async def upload_document(db: Session, file: UploadFile) -> KnowledgeDocument:
    content = await file.read()
    ext = _validate_upload(file.filename or "", len(content))
    disk_path = _save_upload_to_disk(content, ext)

    document = KnowledgeDocument(
        filename=file.filename or disk_path.name,
        storage_path=str(disk_path),
        file_type=ext,
        status="processing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        text = parse_document(disk_path, file.filename or disk_path.name)
        chunks, vectors = _build_chunks_and_vectors(text)
    except ParserError as exc:
        document.status = "failed"
        document.error_message = str(exc)
        db.commit()
        db.refresh(document)
        return document

    try:
        chunk_count = _insert_chunks_and_vectors(db, document.id, chunks, vectors)
        document.status = "ready"
        document.chunk_count = chunk_count
        db.commit()
    except Exception as exc:
        db.rollback()
        document.status = "failed"
        document.error_message = f"Failed to index document: {exc}"
        db.commit()
        db.refresh(document)
        return document

    db.refresh(document)
    return document


async def replace_document(
    db: Session, document: KnowledgeDocument, file: UploadFile
) -> KnowledgeDocument:
    content = await file.read()
    ext = _validate_upload(file.filename or "", len(content))
    new_disk_path = _save_upload_to_disk(content, ext)
    old_disk_path = Path(document.storage_path)

    try:
        text = parse_document(new_disk_path, file.filename or new_disk_path.name)
        chunks, vectors = _build_chunks_and_vectors(text)
    except ParserError as exc:
        # New file failed to parse; keep the existing document/chunks/vectors
        # untouched and report the failure without discarding known-good data.
        new_disk_path.unlink(missing_ok=True)
        raise

    try:
        delete_vectors_for_document(db, document.id)
        db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == document.id).delete()
        chunk_count = _insert_chunks_and_vectors(db, document.id, chunks, vectors)
        document.filename = file.filename or new_disk_path.name
        document.storage_path = str(new_disk_path)
        document.file_type = ext
        document.status = "ready"
        document.chunk_count = chunk_count
        document.error_message = None
        db.commit()
    except Exception:
        db.rollback()
        new_disk_path.unlink(missing_ok=True)
        raise

    old_disk_path.unlink(missing_ok=True)
    db.refresh(document)
    return document


def delete_document(db: Session, document: KnowledgeDocument) -> None:
    delete_vectors_for_document(db, document.id)
    disk_path = Path(document.storage_path)
    db.delete(document)  # cascades to KnowledgeChunk rows via ORM relationship
    db.commit()
    disk_path.unlink(missing_ok=True)
