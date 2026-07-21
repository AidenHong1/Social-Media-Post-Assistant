"""Retrieval of relevant knowledge-base chunks for a generation request."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.knowledge.embedding import embed_text
from app.knowledge.store import knn_search
from app.models import KnowledgeChunk

DEFAULT_TOP_K = 3


def retrieve_relevant_chunks(
    db: Session, topic: str, key_points: list[str], top_k: int = DEFAULT_TOP_K
) -> list[str]:
    """Embed the topic+key_points as a single query and return the text of the
    top_k most similar knowledge chunks, ordered by similarity (most similar
    first). Returns an empty list if no documents have been indexed yet.
    """
    query_text = topic + "\n" + "\n".join(key_points)
    query_vec = embed_text(query_text)
    chunk_ids = knn_search(db, query_vec, top_k)
    if not chunk_ids:
        return []

    rows = db.execute(
        select(KnowledgeChunk.id, KnowledgeChunk.text).where(KnowledgeChunk.id.in_(chunk_ids))
    ).all()
    text_by_id = {row[0]: row[1] for row in rows}
    return [text_by_id[cid] for cid in chunk_ids if cid in text_by_id]


def format_kb_context(chunks: list[str]) -> str:
    if not chunks:
        return ""
    return "\n\n".join(f"[Reference {i + 1}]\n{c}" for i, c in enumerate(chunks))
