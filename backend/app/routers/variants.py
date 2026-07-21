from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Rating, Variant
from app.schemas import RateVariantRequest, RatingOut

router = APIRouter()


@router.post("/variants/{variant_id}/rate", response_model=RatingOut)
def rate_variant(
    variant_id: int,
    req: RateVariantRequest,
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
