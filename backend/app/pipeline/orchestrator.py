import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, Generator
from pydantic import BaseModel

from app.llm.client import LLMClient
from app.pipeline.critique import critique_draft
from app.pipeline.generate import generate_draft
from app.pipeline.rewrite import rewrite_draft
from app.platforms.base import PlatformConstraints


class PipelineResult(BaseModel):
    final_text: str
    draft_text: str
    critique_feedback: str | None
    was_rewritten: bool


def run_single_variant(
    llm: LLMClient,
    topic: str,
    key_points: list[str],
    brand_tone: str,
    constraints: PlatformConstraints,
    kb_context: str = "",
) -> PipelineResult:
    draft = generate_draft(llm, topic, key_points, brand_tone, constraints, kb_context)
    critique = critique_draft(llm, draft, brand_tone, constraints, kb_context)

    if critique.passes:
        return PipelineResult(
            final_text=draft,
            draft_text=draft,
            critique_feedback=critique.feedback,
            was_rewritten=False,
        )

    final = rewrite_draft(llm, draft, critique.feedback, brand_tone, constraints, kb_context)
    return PipelineResult(
        final_text=final,
        draft_text=draft,
        critique_feedback=critique.feedback,
        was_rewritten=True,
    )


def run_platform_variants(
    llm: LLMClient,
    topic: str,
    key_points: list[str],
    brand_tone: str,
    constraints: PlatformConstraints,
    n_variants: int = 2,
    kb_context: str = "",
) -> list[PipelineResult]:
    """并发生成多个变体以提升性能"""
    with ThreadPoolExecutor(max_workers=n_variants) as executor:
        futures = [
            executor.submit(
                run_single_variant, llm, topic, key_points, brand_tone, constraints, kb_context
            )
            for _ in range(n_variants)
        ]
        return [future.result() for future in futures]


def run_platform_variants_stream(
    llm: LLMClient,
    topic: str,
    key_points: list[str],
    brand_tone: str,
    constraints: PlatformConstraints,
    n_variants: int = 2,
    kb_context: str = "",
    on_variant_complete: Callable[[int, PipelineResult], None] | None = None,
) -> Generator[tuple[int, PipelineResult], None, None]:
    """流式生成变体，每完成一个立即yield"""
    with ThreadPoolExecutor(max_workers=n_variants) as executor:
        futures = {
            executor.submit(
                run_single_variant, llm, topic, key_points, brand_tone, constraints, kb_context
            ): idx
            for idx in range(n_variants)
        }

        # 按完成顺序yield结果
        for future in as_completed(futures):
            idx = futures[future]
            result = future.result()
            if on_variant_complete:
                on_variant_complete(idx, result)
            yield idx, result
