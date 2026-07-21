"""Native-SQL helpers for the sqlite-vec virtual table `vec_chunks`.

All functions here take the caller's SQLAlchemy `Session` and execute through
it (never a separate sqlite3 connection), so that inserts/deletes into
`vec_chunks` participate in the same transaction as ordinary ORM writes to
`knowledge_chunks` / `knowledge_documents`. This is required for the
update/delete lifecycle to keep both tables consistent (no orphaned chunks or
vectors) even when something fails mid-operation.
"""

import sqlite_vec
from sqlalchemy import text
from sqlalchemy.orm import Session


def insert_vectors(db: Session, chunk_ids: list[int], vectors: list[list[float]]) -> None:
    for chunk_id, vector in zip(chunk_ids, vectors):
        db.execute(
            text("INSERT INTO vec_chunks (chunk_id, embedding) VALUES (:chunk_id, :embedding)"),
            {"chunk_id": chunk_id, "embedding": sqlite_vec.serialize_float32(vector)},
        )


def delete_vectors_for_document(db: Session, document_id: int) -> None:
    db.execute(
        text(
            "DELETE FROM vec_chunks WHERE chunk_id IN "
            "(SELECT id FROM knowledge_chunks WHERE document_id = :document_id)"
        ),
        {"document_id": document_id},
    )


def knn_search(db: Session, query_vector: list[float], top_k: int) -> list[int]:
    """Return chunk_ids ordered by ascending distance (most similar first)."""
    rows = db.execute(
        text(
            "SELECT chunk_id FROM vec_chunks WHERE embedding MATCH :query_vec "
            "ORDER BY distance LIMIT :k"
        ),
        {"query_vec": sqlite_vec.serialize_float32(query_vector), "k": top_k},
    ).all()
    return [row[0] for row in rows]


def count_vectors(db: Session) -> int:
    return db.execute(text("SELECT count(*) FROM vec_chunks")).scalar_one()
