from app.platforms.base import PlatformConstraints

LINKEDIN_CONSTRAINTS = PlatformConstraints(
    platform_name="linkedin",
    max_chars=3000,
    tone_guide=(
        "Professional, insight-driven, first-person or company voice; "
        "avoid clickbait and overly casual slang."
    ),
    hashtag_style="3-5 relevant hashtags at the end, no hashtags mid-sentence.",
    structural_notes=(
        "Short paragraphs (1-3 sentences), use line breaks, "
        "optional hook line at the top."
    ),
)


class LinkedInAdapter:
    def get_constraints(self) -> PlatformConstraints:
        return LINKEDIN_CONSTRAINTS
