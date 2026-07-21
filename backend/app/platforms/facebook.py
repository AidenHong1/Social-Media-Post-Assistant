from app.platforms.base import PlatformConstraints

FACEBOOK_CONSTRAINTS = PlatformConstraints(
    platform_name="facebook",
    max_chars=1500,
    tone_guide=(
        "Casual, conversational, emotionally engaging; light emoji use is fine; "
        "clear call-to-action."
    ),
    hashtag_style="0-2 hashtags, optional, not required.",
    structural_notes="Short hook-driven opening line, easy to skim, clear CTA at the end.",
)


class FacebookAdapter:
    def get_constraints(self) -> PlatformConstraints:
        return FACEBOOK_CONSTRAINTS
