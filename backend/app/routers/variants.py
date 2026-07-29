import re
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.db import get_db
from app.models import Rating, User, Variant, VariantImage
from app.schemas import (
    ContentSegment,
    ImageSegment,
    RateVariantRequest,
    RatingOut,
    SaveVariantContentRequest,
    TextSegment,
    VariantContentResponse,
)

router = APIRouter()


@router.post("/variants/{variant_id}/rate", response_model=RatingOut)
def rate_variant(
    variant_id: int,
    req: RateVariantRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> RatingOut:
    variant = db.get(Variant, variant_id)
    if variant is None:
        raise HTTPException(status_code=404, detail="Variant not found")

    rating = variant.rating
    if rating is None:
        rating = Rating(variant_id=variant_id, score=req.score, is_favorite=req.is_favorite)
        db.add(rating)
    else:
        rating.score = req.score
        rating.is_favorite = req.is_favorite

    db.commit()
    db.refresh(rating)
    return RatingOut(score=rating.score, is_favorite=rating.is_favorite)


def _split_paragraphs(text: str) -> list[str]:
    """按空行拆分段落，过滤空段落。"""
    parts = re.split(r"\n\n+", text)
    return [p for p in parts if p.strip() != ""] or [text]


def _build_content_response(variant: Variant) -> VariantContentResponse:
    """从 variant.final_text + variant_images 组装出完整的 segments 列表。"""
    images = sorted(variant.images, key=lambda img: img.segment_index)

    if not images:
        segments: list[ContentSegment] = [
            TextSegment(type="text", content=part) for part in _split_paragraphs(variant.final_text)
        ]
        return VariantContentResponse(
            variant_id=variant.id,
            segments=segments,
            updated_at=variant.created_at,
        )

    text_parts = _split_paragraphs(variant.final_text)
    img_by_index = {img.segment_index: img for img in images}
    max_index = max(img_by_index.keys())
    total_len = max(max_index + 1, len(text_parts))

    segments = []
    text_cursor = 0
    latest_updated = variant.created_at

    for i in range(total_len):
        if i in img_by_index:
            img = img_by_index[i]
            if img.updated_at and img.updated_at > latest_updated:
                latest_updated = img.updated_at
            segments.append(
                ImageSegment(
                    type="image",
                    url=img.image_url,
                    filename=img.filename,
                    caption=img.caption,
                    insertedBy=img.inserted_by,
                    promptUsed=img.prompt_used,
                    contextBefore=img.context_before,
                    contextAfter=img.context_after,
                )
            )
        elif text_cursor < len(text_parts):
            segments.append(TextSegment(type="text", content=text_parts[text_cursor]))
            text_cursor += 1

    # 剩余未插入的文本段落追加到末尾
    while text_cursor < len(text_parts):
        segments.append(TextSegment(type="text", content=text_parts[text_cursor]))
        text_cursor += 1

    return VariantContentResponse(
        variant_id=variant.id,
        segments=segments,
        updated_at=latest_updated,
    )


@router.get("/variants/{variant_id}/content", response_model=VariantContentResponse)
def get_variant_content(
    variant_id: int,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> VariantContentResponse:
    variant = db.get(Variant, variant_id)
    if variant is None:
        raise HTTPException(status_code=404, detail="Variant not found")

    return _build_content_response(variant)


@router.put("/variants/{variant_id}/content", response_model=VariantContentResponse)
def save_variant_content(
    variant_id: int,
    req: SaveVariantContentRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
) -> VariantContentResponse:
    variant = db.get(Variant, variant_id)
    if variant is None:
        raise HTTPException(status_code=404, detail="Variant not found")

    # 清空旧的图片记录
    db.query(VariantImage).filter(VariantImage.variant_id == variant_id).delete()

    # 重新写入图片记录，并重建 final_text（仅由 text segment 拼接）
    text_contents = []
    now = datetime.utcnow()
    for idx, seg in enumerate(req.segments):
        if seg.type == "text":
            text_contents.append(seg.content)
        else:
            image = VariantImage(
                variant_id=variant_id,
                segment_index=idx,
                image_url=seg.url,
                filename=seg.filename,
                caption=seg.caption,
                inserted_by=seg.insertedBy,
                prompt_used=seg.promptUsed,
                context_before=seg.contextBefore,
                context_after=seg.contextAfter,
                created_at=now,
                updated_at=now,
            )
            db.add(image)

    if text_contents:
        variant.final_text = "\n\n".join(text_contents)

    db.commit()
    db.refresh(variant)

    return _build_content_response(variant)
