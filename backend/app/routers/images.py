from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Variant
from app.schemas import (
    AutoImageRequest,
    AutoImageResponse,
    ImageGenerateRequest,
    ImageGenerateResponse,
)
from app.services.image_service import image_service

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


@router.post("/auto-for-variant", response_model=AutoImageResponse)
async def auto_image_for_variant(req: AutoImageRequest, db: Session = Depends(get_db)):
    """AI analyzes variant text and auto-generates appropriate image."""
    _check_enabled()

    variant = db.query(Variant).filter(Variant.id == req.variant_id).first()
    if not variant:
        raise HTTPException(404, "Variant not found")

    result = await image_service.auto_for_variant(variant.final_text, variant.platform)

    return AutoImageResponse(**result)


@router.get("/files/{filename}")
async def serve_image(filename: str):
    """Serve image file (no auth required - browser <img> tags can't send Bearer token)."""
    # Prevent path traversal
    safe_filename = Path(filename).name
    filepath = Path(settings.image_storage_dir) / safe_filename

    if not filepath.exists():
        raise HTTPException(404, "Image not found")

    return FileResponse(filepath, media_type="image/png")
