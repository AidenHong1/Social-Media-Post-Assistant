from app.platforms.base import PlatformAdapter
from app.platforms.facebook import FacebookAdapter
from app.platforms.linkedin import LinkedInAdapter

PLATFORM_ADAPTERS: dict[str, PlatformAdapter] = {
    "linkedin": LinkedInAdapter(),
    "facebook": FacebookAdapter(),
}


def get_adapter(name: str) -> PlatformAdapter:
    try:
        return PLATFORM_ADAPTERS[name]
    except KeyError:
        raise ValueError(f"Unsupported platform: {name}")
