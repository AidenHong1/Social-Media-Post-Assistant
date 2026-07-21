"""Split parsed document text into overlapping, sentence-boundary-aware chunks."""

import re

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n\s*\n")

TARGET_CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
HARD_MAX_SENTENCE_SIZE = 1200


def _split_sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]
    return parts


def _hard_split(sentence: str, max_size: int) -> list[str]:
    return [sentence[i : i + max_size] for i in range(0, len(sentence), max_size)]


def chunk_text(
    text: str,
    target_size: int = TARGET_CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
    hard_max: int = HARD_MAX_SENTENCE_SIZE,
) -> list[str]:
    """Chunk text into ~target_size character pieces, breaking on sentence
    boundaries where possible, with a character-based overlap between chunks.
    """
    sentences: list[str] = []
    for raw_sentence in _split_sentences(text):
        if len(raw_sentence) > hard_max:
            sentences.extend(_hard_split(raw_sentence, hard_max))
        else:
            sentences.append(raw_sentence)

    if not sentences:
        return []

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) > target_size and current:
            chunks.append(current)
            # start next chunk with overlap tail of the previous chunk
            tail = current[-overlap:] if len(current) > overlap else current
            current = f"{tail} {sentence}".strip()
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks
