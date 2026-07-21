from app.platforms.base import PlatformConstraints


def _constraints_block(constraints: PlatformConstraints) -> str:
    return (
        f"Platform: {constraints.platform_name}\n"
        f"Max characters: {constraints.max_chars}\n"
        f"Tone guide: {constraints.tone_guide}\n"
        f"Hashtag style: {constraints.hashtag_style}\n"
        f"Structural notes: {constraints.structural_notes}"
    )


def _kb_context_block(kb_context: str) -> str:
    if not kb_context:
        return ""
    return f"Company reference facts (ground the post in these where relevant):\n{kb_context}\n\n"


def build_generation_prompt(
    topic: str,
    key_points: list[str],
    brand_tone: str,
    constraints: PlatformConstraints,
    kb_context: str = "",
) -> tuple[str, str]:
    system = (
        "You are an expert social media copywriter who writes platform-native posts. "
        "Follow the platform constraints exactly. Output ONLY the post text, no preamble, "
        "no markdown code fences, no explanations.\n\n" + _constraints_block(constraints)
    )
    points_block = "\n".join(f"- {p}" for p in key_points) if key_points else "(none provided)"
    tone_line = f"Additionally, match this brand voice: {brand_tone}" if brand_tone else ""
    user = (
        f"{_kb_context_block(kb_context)}"
        f"Topic: {topic}\n"
        f"Key points to cover:\n{points_block}\n"
        f"{tone_line}\n\n"
        "Write the post now."
    )
    return system, user


def build_critique_prompt(
    draft: str,
    brand_tone: str,
    constraints: PlatformConstraints,
    kb_context: str = "",
) -> tuple[str, str]:
    fact_check_rule = (
        "Also check whether the draft conflicts with the provided company reference facts. "
        "Set passes=false if it contradicts them.\n\n"
        if kb_context
        else ""
    )
    system = (
        "You are a strict editor reviewing a social media post draft against platform "
        "constraints and brand voice. Respond with ONLY a compact JSON object of the form "
        '{"passes": true|false, "feedback": "short actionable feedback"}. '
        "No markdown, no extra text.\n\n" + fact_check_rule + _constraints_block(constraints)
    )
    tone_line = f"Brand voice to match: {brand_tone}" if brand_tone else ""
    user = (
        f"{_kb_context_block(kb_context)}"
        f"{tone_line}\n\n"
        "Draft post to review:\n"
        f"---\n{draft}\n---\n\n"
        "Does this draft satisfy the platform constraints, tone guide, and brand voice? "
        "Set passes=false if it is too long, off-tone, generic/clichéd, or has a weak hook. "
        "Return the JSON object now."
    )
    return system, user


def build_rewrite_prompt(
    draft: str,
    critique_feedback: str,
    brand_tone: str,
    constraints: PlatformConstraints,
    kb_context: str = "",
) -> tuple[str, str]:
    system = (
        "You are an expert social media copywriter revising a draft based on editor feedback. "
        "Output ONLY the revised post text, no preamble, no markdown code fences.\n\n"
        + _constraints_block(constraints)
    )
    tone_line = f"Brand voice to match: {brand_tone}" if brand_tone else ""
    user = (
        f"{_kb_context_block(kb_context)}"
        f"Original draft:\n---\n{draft}\n---\n\n"
        f"Editor feedback to address:\n{critique_feedback}\n\n"
        f"{tone_line}\n\n"
        "Rewrite the post now, addressing the feedback."
    )
    return system, user
