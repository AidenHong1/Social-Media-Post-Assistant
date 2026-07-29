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


class Template(Base):
    __tablename__ = "templates"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str | None]
    category: Mapped[str] = mapped_column(String(50))
    platform: Mapped[str] = mapped_column(String(20))  # linkedin | facebook | both
    topic: Mapped[str | None]
    key_points: Mapped[str]  # JSON-encoded list[str]
    brand_tone: Mapped[str] = mapped_column(default="")
    is_builtin: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


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


class VariantImage(Base):
    __tablename__ = "variant_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    variant_id: Mapped[int] = mapped_column(ForeignKey("variants.id", ondelete="CASCADE"))
    segment_index: Mapped[int]  # 在 segments 数组中的位置
    image_url: Mapped[str] = mapped_column(String(500))  # /api/images/files/{filename} 或外链
    filename: Mapped[str | None] = mapped_column(String(255))  # 本地文件名
    caption: Mapped[str | None]
    inserted_by: Mapped[str] = mapped_column(String(10))  # 'manual' | 'ai'
    prompt_used: Mapped[str | None]  # AI生成时使用的 prompt
    context_before: Mapped[str | None]  # 插入点前的上下文
    context_after: Mapped[str | None]  # 插入点后的上下文
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    variant: Mapped["Variant"] = relationship(back_populates="images")


# 更新 Variant 模型，添加 images 关系
Variant.images = relationship(
    "VariantImage",
    back_populates="variant",
    cascade="all, delete-orphan",
    order_by="VariantImage.segment_index"
)
