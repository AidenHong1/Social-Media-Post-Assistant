import json

from fastapi import HTTPException
from openai import APIError, APIStatusError, APITimeoutError
from sqlalchemy.orm import Session

from app.knowledge.retriever import format_kb_context, retrieve_relevant_chunks
from app.llm.client import LLMClient
from app.models import GenerationRequest, Variant
from app.pipeline.orchestrator import run_platform_variants
from app.platforms.registry import get_adapter
from app.schemas import GenerateRequest


def create_generation(
    db: Session, llm: LLMClient, req: GenerateRequest
) -> GenerationRequest:
    db_request = GenerationRequest(
        topic=req.topic,
        key_points=json.dumps(req.key_points),
        brand_tone=req.brand_tone,
        platforms=json.dumps(req.platforms),
        n_variants=req.n_variants,
    )
    db.add(db_request)
    db.flush()

    kb_context = format_kb_context(
        retrieve_relevant_chunks(db, req.topic, req.key_points)
    )

    try:
        for platform in req.platforms:
            adapter = get_adapter(platform)
            constraints = adapter.get_constraints()
            results = run_platform_variants(
                llm,
                topic=req.topic,
                key_points=req.key_points,
                brand_tone=req.brand_tone,
                constraints=constraints,
                n_variants=req.n_variants,
                kb_context=kb_context,
            )
            for idx, result in enumerate(results):
                db.add(
                    Variant(
                        request_id=db_request.id,
                        platform=platform,
                        variant_index=idx,
                        draft_text=result.draft_text,
                        final_text=result.final_text,
                        critique_feedback=result.critique_feedback,
                        was_rewritten=result.was_rewritten,
                    )
                )
    except (APIError, APIStatusError, APITimeoutError) as exc:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail=f"LLM provider request failed: {exc}",
        ) from exc

    db.commit()
    db.refresh(db_request)
    return db_request
