import json
from concurrent.futures import Future, ThreadPoolExecutor
from typing import AsyncGenerator

from fastapi import HTTPException
from openai import APIError, APIStatusError, APITimeoutError
from sqlalchemy.orm import Session

from app.knowledge.retriever import format_kb_context, retrieve_relevant_chunks
from app.llm.client import LLMClient
from app.models import GenerationRequest, Variant
from app.pipeline.orchestrator import PipelineResult, run_platform_variants, run_platform_variants_stream
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

    def process_platform(platform: str):
        """处理单个平台的所有变体"""
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
        return platform, results

    try:
        # 并发处理所有平台
        with ThreadPoolExecutor(max_workers=len(req.platforms)) as executor:
            futures = [executor.submit(process_platform, platform) for platform in req.platforms]
            all_results = [future.result() for future in futures]

        # 保存所有结果到数据库
        for platform, results in all_results:
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


async def create_generation_stream(
    db: Session, llm: LLMClient, req: GenerateRequest
) -> AsyncGenerator[dict, None]:
    """流式生成，逐个yield完成的变体结果"""
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

    def process_platform_stream(platform: str):
        """流式处理单个平台的所有变体"""
        try:
            adapter = get_adapter(platform)
            constraints = adapter.get_constraints()
            # 使用流式生成器
            for idx, result in run_platform_variants_stream(
                llm,
                topic=req.topic,
                key_points=req.key_points,
                brand_tone=req.brand_tone,
                constraints=constraints,
                n_variants=req.n_variants,
                kb_context=kb_context,
            ):
                yield platform, idx, result, None
        except Exception as e:
            yield platform, -1, None, str(e)

    try:
        # 并发处理所有平台，流式返回结果
        with ThreadPoolExecutor(max_workers=len(req.platforms)) as executor:
            futures = [
                executor.submit(lambda p=platform: list(process_platform_stream(p)), platform)
                for platform in req.platforms
            ]

            # 使用 as_completed 逐个获取完成的平台结果
            from concurrent.futures import as_completed

            for future in as_completed(futures):
                platform_results = future.result()

                for platform, idx, result, error in platform_results:
                    if error:
                        # 发送错误事件
                        yield {
                            "type": "error",
                            "platform": platform,
                            "message": error,
                        }
                        continue

                    # 保存并发送变体
                    variant = Variant(
                        request_id=db_request.id,
                        platform=platform,
                        variant_index=idx,
                        draft_text=result.draft_text,
                        final_text=result.final_text,
                        critique_feedback=result.critique_feedback,
                        was_rewritten=result.was_rewritten,
                    )
                    db.add(variant)
                    db.flush()
                    db.refresh(variant)

                    # 发送变体完成事件
                    yield {
                        "type": "variant",
                        "data": {
                            "id": variant.id,
                            "platform": variant.platform,
                            "variant_index": variant.variant_index,
                            "final_text": variant.final_text,
                            "draft_text": variant.draft_text,
                            "critique_feedback": variant.critique_feedback,
                            "was_rewritten": variant.was_rewritten,
                            "rating": None,
                        },
                    }

        # 发送完成事件
        db.commit()
        db.refresh(db_request)
        yield {
            "type": "complete",
            "data": {
                "request_id": db_request.id,
                "topic": db_request.topic,
                "brand_tone": db_request.brand_tone,
                "created_at": db_request.created_at.isoformat(),
            },
        }

    except (APIError, APIStatusError, APITimeoutError) as exc:
        db.rollback()
        yield {
            "type": "error",
            "message": f"LLM provider request failed: {exc}",
        }
