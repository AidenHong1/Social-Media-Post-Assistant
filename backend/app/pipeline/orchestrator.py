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
    return [
        run_single_variant(llm, topic, key_points, brand_tone, constraints, kb_context)
        for _ in range(n_variants)
    ]
