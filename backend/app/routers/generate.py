import json
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth import get_current_active_user
from app.db import get_db
from app.llm.client import LLMClient, get_llm_client
from app.models import User
from app.schemas import GenerateRequest, GenerateResponse
from app.services.generation_service import create_generation, create_generation_stream

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


@router.post("/generate-stream")
async def generate_stream(
    req: GenerateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db),
    llm: LLMClient = Depends(get_llm_client),
):
    """流式生成端点，使用 Server-Sent Events (SSE) 逐个返回完成的变体"""

    async def event_generator():
        try:
            async for event in create_generation_stream(db, llm, req):
                # SSE 格式：data: {json}\n\n
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_event = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 nginx 缓冲
        },
    )
