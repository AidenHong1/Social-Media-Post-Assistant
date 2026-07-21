"""Local embedding model wrapper (no external API calls)."""

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

_model = None


def get_embedding_model():
    """Lazily load and cache the sentence-transformers model as a module-level
    singleton. Called once eagerly at app startup to pre-warm, and reused for
    every subsequent embed call.
    """
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts, returning normalized 384-dim vectors."""
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vectors]


def embed_text(text: str) -> list[float]:
    """Embed a single piece of text (e.g. a retrieval query)."""
    return embed_texts([text])[0]
