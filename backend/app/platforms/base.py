from typing import Protocol

from pydantic import BaseModel


class PlatformConstraints(BaseModel):
    platform_name: str
    max_chars: int
    tone_guide: str
    hashtag_style: str
    structural_notes: str


class PlatformAdapter(Protocol):
    def get_constraints(self) -> PlatformConstraints: ...
