from app.llm.client import LLMClient
from app.pipeline.prompts import build_rewrite_prompt
from app.platforms.base import PlatformConstraints


def rewrite_draft(
    llm: LLMClient,
    draft: str,
    critique_feedback: str,
    brand_tone: str,
    constraints: PlatformConstraints,
    kb_context: str = "",
) -> str:
    system, user = build_rewrite_prompt(draft, critique_feedback, brand_tone, constraints, kb_context)
    return llm.chat(system, user).strip()
