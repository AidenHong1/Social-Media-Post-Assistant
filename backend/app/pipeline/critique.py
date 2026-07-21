import json
import re

from pydantic import BaseModel

from app.llm.client import LLMClient
from app.pipeline.prompts import build_critique_prompt
from app.platforms.base import PlatformConstraints


class CritiqueResult(BaseModel):
    passes: bool
    feedback: str


def _extract_json_block(raw: str) -> str:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    return match.group(0) if match else raw


def parse_critique_response(raw: str) -> CritiqueResult:
    try:
        data = json.loads(_extract_json_block(raw))
        return CritiqueResult(
            passes=bool(data.get("passes", False)),
            feedback=str(data.get("feedback", "")),
        )
    except (json.JSONDecodeError, AttributeError, TypeError):
        return CritiqueResult(passes=False, feedback=raw.strip())


def critique_draft(
    llm: LLMClient,
    draft: str,
    brand_tone: str,
    constraints: PlatformConstraints,
    kb_context: str = "",
) -> CritiqueResult:
    system, user = build_critique_prompt(draft, brand_tone, constraints, kb_context)
    raw = llm.chat(system, user)
    return parse_critique_response(raw)
