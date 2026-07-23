from datetime import datetime

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    hashed_password: Mapped[str]
    full_name: Mapped[str | None]
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class GenerationRequest(Base):
    __tablename__ = "generation_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str]
    key_points: Mapped[str]  # JSON-encoded list[str]
    brand_tone: Mapped[str]
    platforms: Mapped[str]  # JSON-encoded list[str]
    n_variants: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    variants: Mapped[list["Variant"]] = relationship(
        back_populates="request", cascade="all, delete-orphan"
    )


class Variant(Base):
    __tablename__ = "variants"

    id: Mapped[int] = mapped_column(primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("generation_requests.id"))
    platform: Mapped[str]
    variant_index: Mapped[int]
    draft_text: Mapped[str]
    final_text: Mapped[str]
    critique_feedback: Mapped[str | None]
    was_rewritten: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    request: Mapped["GenerationRequest"] = relationship(back_populates="variants")
    rating: Mapped["Rating | None"] = relationship(
        back_populates="variant", uselist=False, cascade="all, delete-orphan"
    )


class Rating(Base):
    __tablename__ = "ratings"

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(
        ForeignKey("variants.id"), unique=True
    )
    score: Mapped[int]
    is_favorite: Mapped[bool] = mapped_column(default=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    variant: Mapped["Variant"] = relationship(back_populates="rating")


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
    storage_path: Mapped[str]
    file_type: Mapped[str]  # pdf / docx / txt
    status: Mapped[str]  # processing / ready / failed
    error_message: Mapped[str | None]
    chunk_count: Mapped[int] = mapped_column(default=0)
    uploaded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, onupdate=datetime.utcnow
    )

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)  # also used as vec_chunks.chunk_id
    document_id: Mapped[int] = mapped_column(ForeignKey("knowledge_documents.id"))
    chunk_index: Mapped[int]
    text: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    document: Mapped["KnowledgeDocument"] = relationship(back_populates="chunks")
