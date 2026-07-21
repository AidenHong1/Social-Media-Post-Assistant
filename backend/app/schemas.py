from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

PlatformName = Literal["linkedin", "facebook"]


class GenerateRequest(BaseModel):
    topic: str = Field(min_length=1)
    key_points: list[str] = []
    brand_tone: str = ""
    platforms: list[PlatformName] = Field(min_length=1)
    n_variants: int = Field(default=2, ge=1, le=3)


class RatingOut(BaseModel):
    score: int
    is_favorite: bool

    model_config = {"from_attributes": True}


class VariantOut(BaseModel):
    id: int
    platform: str
    variant_index: int
    final_text: str
    draft_text: str
    critique_feedback: str | None
    was_rewritten: bool
    rating: RatingOut | None

    model_config = {"from_attributes": True}


class GenerateResponse(BaseModel):
    request_id: int
    topic: str
    brand_tone: str
    created_at: datetime
    variants: list[VariantOut]


class HistoryItem(BaseModel):
    request_id: int
    topic: str
    platforms: list[str]
    created_at: datetime
    variant_count: int


class RateVariantRequest(BaseModel):
    score: int = Field(ge=1, le=5)
    is_favorite: bool = False


DocumentStatus = Literal["processing", "ready", "failed"]


class DocumentOut(BaseModel):
    id: int
    filename: str
    file_type: str
    status: DocumentStatus
    chunk_count: int
    error_message: str | None
    uploaded_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
