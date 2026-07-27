"""
增强版提示词系统 - 融入高流量社交媒体写作技巧

核心原则:
- 强开头 + 高相关性 + 可传播信息 + 明确互动信号
- LinkedIn: 职业价值、行业洞察、方法论、案例复盘
- Facebook: 情绪共鸣、生活化表达、社群互动、故事传播
"""

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


def _get_platform_writing_principles(platform_name: str) -> str:
    """根据平台返回差异化的写作原则"""
    platform_lower = platform_name.lower()

    if "linkedin" in platform_lower:
        return """
LinkedIn 高流量内容原则:
- 用户转发是为了展示专业性,所以内容要有"可引用价值"
- 优先使用: 行业洞察、实战复盘、数据案例、职业认知
- 开头必须体现职业价值或认知升级
- 结构: 问题/观察 → 经验/方法 → 可复用结论
"""
    elif "facebook" in platform_lower:
        return """
Facebook 高流量内容原则:
- 用户分享是为了表达自己,所以内容要有"情绪共鸣"
- 优先使用: 故事、共鸣观点、互动提问、实用清单
- 开头必须制造情绪连接或好奇心
- 结构: 场景/故事 → 情绪/观点 → 互动引导
"""
    else:
        return """
通用社交媒体高流量原则:
- 开头2句决定用户是否继续阅读
- 每篇只讲一个核心观点
- 提供可转述、可分享的信息
- 结尾设计明确的互动动作
"""


def _get_hook_examples(platform_name: str) -> str:
    """提供平台相关的强开头示例"""
    platform_lower = platform_name.lower()

    if "linkedin" in platform_lower:
        return """
强开头类型(LinkedIn):
- 反常识: "大多数团队在做XX时,第一步就错了"
- 明确结果: "过去6个月,我们把XX从30秒压到8秒"
- 真实经历: "第一次做XX项目时,我低估了这个问题"
- 行业洞察: "为什么越来越多公司开始重视XX,而不是XX"
"""
    elif "facebook" in platform_lower:
        return """
强开头类型(Facebook):
- 故事切入: "昨天和客户的对话,让我重新理解了XX"
- 情绪共鸣: "成年人最大的疲惫,不是忙,而是XX"
- 冲突感: "我差点放弃这个项目,但最后XX让我改了想法"
- 直接提问: "如果你只能保留一个习惯,你会选哪个?"
"""
    else:
        return """
强开头类型:
- 使用反常识、明确结果、强问题、真实经历或冲突感
- 避免空泛开头如"今天想聊聊XX"
"""


def _get_content_avoid_list() -> str:
    """返回应避免的内容特征"""
    return """
必须避免的内容特征:
❌ 太像广告: "我们公司很专业/产品功能很多/欢迎咨询"
❌ 太空泛: "坚持就是胜利/努力很重要" 等鸡汤
❌ 没有人味: 只有结论,没有场景/经历/情绪/细节
❌ 一上来就讲自己: 先讲用户问题,再讲你的经验
❌ 低信息密度: 大段空话、套话、自夸
"""


def build_generation_prompt(
    topic: str,
    key_points: list[str],
    brand_tone: str,
    constraints: PlatformConstraints,
    kb_context: str = "",
) -> tuple[str, str]:
    """构建生成提示词 - 融入高流量写作技巧"""
    platform_principles = _get_platform_writing_principles(constraints.platform_name)
    hook_examples = _get_hook_examples(constraints.platform_name)
    avoid_list = _get_content_avoid_list()

    system = (
        "You are an expert social media copywriter specializing in high-engagement content. "
        "Your posts consistently achieve high reach and interaction because you understand "
        "platform algorithms reward: long dwell time, genuine discussion, shares, and saves.\n\n"
        f"{platform_principles}\n"
        f"{hook_examples}\n"
        f"{avoid_list}\n\n"
        "CRITICAL STRUCTURE REQUIREMENTS:\n"
        "1. Opening (first 1-2 sentences): Must hook immediately with value/insight/emotion\n"
        "2. Body: High information density - every sentence adds new value\n"
        "3. Closing: Include clear engagement prompt (question/invitation to share)\n\n"
        "Output ONLY the post text, no preamble, no markdown code fences, no explanations.\n\n"
        + _constraints_block(constraints)
    )

    points_block = "\n".join(f"- {p}" for p in key_points) if key_points else "(none provided)"
    tone_line = f"Brand voice to match: {brand_tone}" if brand_tone else ""

    user = (
        f"{_kb_context_block(kb_context)}"
        f"Topic: {topic}\n"
        f"Key points to cover:\n{points_block}\n"
        f"{tone_line}\n\n"
        "WRITING CHECKLIST:\n"
        "✓ Does the opening hook in 1-2 sentences?\n"
        "✓ Is there a clear core insight/story/value proposition?\n"
        "✓ Does it provide shareable/quotable information?\n"
        "✓ Does the ending invite specific interaction?\n"
        "✓ Is it focused on user value, not self-promotion?\n\n"
        "Write the post now."
    )

    return system, user


def build_critique_prompt(
    draft: str,
    brand_tone: str,
    constraints: PlatformConstraints,
    kb_context: str = "",
) -> tuple[str, str]:
    """构建评审提示词 - 使用增强的评判标准"""
    platform_name = constraints.platform_name.lower()

    if "linkedin" in platform_name:
        platform_criteria = (
            "- Professional value: Does it help readers grow/learn/improve?\n"
            "- Credibility: Is there evidence/data/real experience?\n"
            "- Shareability: Would professionals want to repost this?\n"
        )
    elif "facebook" in platform_name:
        platform_criteria = (
            "- Emotional resonance: Does it create connection/empathy?\n"
            "- Relatability: Can readers see themselves in this?\n"
            "- Conversation starter: Will it spark genuine discussion?\n"
        )
    else:
        platform_criteria = (
            "- Value delivery: Does it provide clear takeaways?\n"
            "- Engagement potential: Will users interact with this?\n"
        )

    fact_check_rule = (
        "Also check whether the draft conflicts with the provided company reference facts. "
        "Set passes=false if it contradicts them.\n\n"
        if kb_context
        else ""
    )

    system = (
        "You are a strict editor reviewing social media content for viral potential and quality. "
        "You understand what drives algorithmic distribution and genuine engagement.\n\n"
        "EVALUATION CRITERIA:\n"
        "1. HOOK STRENGTH (first 1-2 sentences):\n"
        "   - Does it create immediate value/curiosity/emotion?\n"
        "   - Would users stop scrolling?\n"
        "   ❌ Fail if: generic opening, weak hook, or buries the lead\n\n"
        "2. INFORMATION DENSITY:\n"
        "   - Does every paragraph add new insight?\n"
        "   - Is there shareable/quotable content?\n"
        "   ❌ Fail if: fluffy filler, obvious statements, or pure self-promotion\n\n"
        "3. ENGAGEMENT DESIGN:\n"
        "   - Does it end with clear call to interaction?\n"
        "   - Are there discussion triggers throughout?\n"
        "   ❌ Fail if: no engagement prompt or ends weakly\n\n"
        f"4. PLATFORM FIT:\n{platform_criteria}\n"
        "5. AVOIDING RED FLAGS:\n"
        "   ❌ Sounds like an ad\n"
        "   ❌ Generic motivational quotes\n"
        "   ❌ No human voice/personality\n"
        "   ❌ Starts with self-promotion\n\n"
        f"{fact_check_rule}"
        'Respond with ONLY a compact JSON object: {"passes": true|false, "feedback": "specific actionable feedback"}. '
        "No markdown, no extra text.\n\n"
        + _constraints_block(constraints)
    )

    tone_line = f"Brand voice to match: {brand_tone}" if brand_tone else ""

    user = (
        f"{_kb_context_block(kb_context)}"
        f"{tone_line}\n\n"
        "Draft post to review:\n"
        f"---\n{draft}\n---\n\n"
        "Evaluate against all criteria above. Set passes=false if:\n"
        "- Weak/generic opening hook\n"
        "- Low information density or fluffy content\n"
        "- Missing engagement prompt\n"
        "- Too promotional or ad-like\n"
        "- Exceeds character limit\n"
        "- Off-brand tone\n\n"
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
    """构建重写提示词 - 强调核心写作原则"""
    hook_examples = _get_hook_examples(constraints.platform_name)

    system = (
        "You are an expert social media copywriter revising content based on editorial feedback. "
        "You specialize in transforming weak drafts into high-engagement posts.\n\n"
        f"{hook_examples}\n"
        "REWRITE PRIORITIES:\n"
        "1. Fix the hook first - make the opening irresistible\n"
        "2. Increase information density - every sentence must earn its place\n"
        "3. Add engagement triggers - specific questions or discussion prompts\n"
        "4. Remove promotional language - focus on user value\n"
        "5. Inject personality - use real details/experience/voice\n\n"
        "Output ONLY the revised post text, no preamble, no markdown code fences.\n\n"
        + _constraints_block(constraints)
    )

    tone_line = f"Brand voice to match: {brand_tone}" if brand_tone else ""

    user = (
        f"{_kb_context_block(kb_context)}"
        f"Original draft:\n---\n{draft}\n---\n\n"
        f"Editor feedback to address:\n{critique_feedback}\n\n"
        f"{tone_line}\n\n"
        "BEFORE YOU REWRITE, ASK:\n"
        "- What's the one core insight/story/value here?\n"
        "- How can I make the first sentence stop the scroll?\n"
        "- What specific action/discussion do I want to trigger?\n\n"
        "Rewrite the post now, addressing the feedback."
    )

    return system, user
