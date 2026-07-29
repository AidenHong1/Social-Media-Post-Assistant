import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Variant
from app.schemas import (
    AutoImageRequest,
    AutoImageResponse,
    AutoMultiImageRequest,
    AutoMultiImageResponse,
    GenerateContextualImageRequest,
    GenerateContextualImageResponse,
    ImageGenerateRequest,
    ImageGenerateResponse,
    ImageUploadResponse,
)
from app.services.image_service import ImageTooLargeError, UnsupportedImageTypeError, image_service

router = APIRouter(prefix="/images", tags=["images"])


def _check_enabled():
    if not settings.image_generation_enabled:
        raise HTTPException(
            status_code=400,
            detail="Image generation is disabled. Set IMAGE_GENERATION_ENABLED=true in .env to enable.",
        )


@router.post("/generate", response_model=ImageGenerateResponse)
async def generate_image(req: ImageGenerateRequest):
    """Generate image from manual prompt."""
    _check_enabled()

    image_url, filename = await image_service.generate_image(req.prompt, req.size)

    return ImageGenerateResponse(
        image_url=image_url,
        prompt_used=req.prompt,
        filename=filename,
    )


@router.post("/upload", response_model=ImageUploadResponse, status_code=201)
async def upload_image(file: UploadFile = File(...)):
    """从本地文件选择器上传图片。"""
    content = await file.read()
    try:
        image_url, filename = image_service.save_uploaded_image(
            file.filename or "", file.content_type, content
        )
    except (UnsupportedImageTypeError, ImageTooLargeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ImageUploadResponse(image_url=image_url, filename=filename)


@router.post("/auto-for-variant", response_model=AutoImageResponse)
async def auto_image_for_variant(req: AutoImageRequest, db: Session = Depends(get_db)):
    """AI analyzes variant text and auto-generates appropriate image."""
    _check_enabled()

    variant = db.query(Variant).filter(Variant.id == req.variant_id).first()
    if not variant:
        raise HTTPException(404, "Variant not found")

    result = await image_service.auto_for_variant(variant.final_text, variant.platform)

    return AutoImageResponse(**result)


@router.post("/auto-multi-for-variant", response_model=AutoMultiImageResponse)
async def auto_multi_image_for_variant(req: AutoMultiImageRequest, db: Session = Depends(get_db)):
    """AI 分析变体文案结构，智能选择多个插入位置并分别生成匹配的图片（流量最大化）。"""
    _check_enabled()

    variant = db.query(Variant).filter(Variant.id == req.variant_id).first()
    if not variant:
        raise HTTPException(404, "Variant not found")

    result = await image_service.auto_multi_for_variant(
        variant.final_text, variant.platform, max_images=req.max_images
    )

    return AutoMultiImageResponse(**result)


@router.post("/generate-contextual", response_model=GenerateContextualImageResponse)
async def generate_contextual_image(req: GenerateContextualImageRequest, db: Session = Depends(get_db)):
    """根据插入位置的上下文（前后文本 + 可选用户提示词）智能生成匹配的图片。"""
    _check_enabled()

    variant = db.query(Variant).filter(Variant.id == req.variant_id).first()
    if not variant:
        raise HTTPException(404, "Variant not found")

    result = await image_service.generate_contextual_image(
        context_before=req.context_before,
        context_after=req.context_after,
        user_prompt=req.user_prompt,
        size=req.size,
    )

    return GenerateContextualImageResponse(**result)


@router.get("/files/{filename}")
async def serve_image(filename: str):
    """Serve image file (no auth required - browser <img> tags can't send Bearer token)."""
    # Prevent path traversal
    safe_filename = Path(filename).name
    filepath = Path(settings.image_storage_dir) / safe_filename

    if not filepath.exists():
        raise HTTPException(404, "Image not found")

    media_type = mimetypes.guess_type(safe_filename)[0] or "image/png"
    return FileResponse(filepath, media_type=media_type)
