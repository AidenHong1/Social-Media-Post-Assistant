from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.db import get_db
from app.llm.client import LLMClient, get_llm_client
from app.models import User
from app.schemas import GenerateRequest, GenerateResponse
from app.services.generation_service import create_generation

router = APIRouter()


@router.post("/generate", response_model=GenerateResponse)
def generate(
    req: GenerateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
) -> GenerateResponse:
    db_request = create_generation(db, llm, req)
    return GenerateResponse(
        request_id=db_request.id,
        topic=db_request.topic,
        brand_tone=db_request.brand_tone,
        created_at=db_request.created_at,
        variants=list(db_request.variants),
    )
