from app.llm.client import LLMClient
from app.pipeline.prompts import build_generation_prompt
from app.platforms.base import PlatformConstraints


def generate_draft(
    llm: LLMClient,
    topic: str,
    key_points: list[str],
    brand_tone: str,
    constraints: PlatformConstraints,
    kb_context: str = "",
) -> str:
    system, user = build_generation_prompt(topic, key_points, brand_tone, constraints, kb_context)
    return llm.chat(system, user).strip()
