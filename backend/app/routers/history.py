import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import GenerationRequest
from app.schemas import GenerateResponse, HistoryItem

router = APIRouter()


@router.get("/history", response_model=list[HistoryItem])
def list_history(db: Session = Depends(get_db)) -> list[HistoryItem]:
    stmt = (
        select(GenerationRequest)
        .order_by(GenerationRequest.created_at.desc())
        .limit(50)
    )
    requests = db.execute(stmt).scalars().all()
    return [
        HistoryItem(
            request_id=r.id,
            topic=r.topic,
            platforms=json.loads(r.platforms),
            created_at=r.created_at,
            variant_count=len(r.variants),
        )
        for r in requests
    ]


@router.get("/history/{request_id}", response_model=GenerateResponse)
def get_history_item(request_id: int, db: Session = Depends(get_db)) -> GenerateResponse:
    db_request = db.get(GenerationRequest, request_id)
    if db_request is None:
        raise HTTPException(status_code=404, detail="Request not found")
    return GenerateResponse(
        request_id=db_request.id,
        topic=db_request.topic,
        brand_tone=db_request.brand_tone,
        created_at=db_request.created_at,
        variants=list(db_request.variants),
    )
