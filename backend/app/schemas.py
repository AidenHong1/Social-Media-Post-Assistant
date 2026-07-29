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


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    category: str = Field(min_length=1, max_length=50)
    platform: str = "both"
    topic: str | None = None
    key_points: list[str] = []
    brand_tone: str = ""


class TemplateOut(BaseModel):
    id: int
    name: str
    description: str | None
    category: str
    platform: str
    topic: str | None
    key_points: list[str]
    brand_tone: str
    is_builtin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)
    size: str = "1792x1024"


class ImageGenerateResponse(BaseModel):
    image_url: str
    prompt_used: str
    filename: str


class AutoImageRequest(BaseModel):
    variant_id: int


class AutoImageResponse(BaseModel):
    image_url: str
    insertion_position: str  # beginning | after_hook | before_cta | end
    prompt_used: str
    caption: str
    filename: str


class ImageSuggestion(BaseModel):
    """单个图片建议（位置 + prompt + caption）"""
    insertion_index: int  # 插入到 segments[insertion_index] 之前
    image_prompt: str
    caption: str


class GeneratedPositionedImage(BaseModel):
    """已生成的图片，携带其插入位置索引"""
    image_url: str
    insertion_index: int
    prompt_used: str
    caption: str
    filename: str


class AutoMultiImageRequest(BaseModel):
    variant_id: int
    max_images: int = Field(default=3, ge=1, le=5)  # 最多生成几张图


class AutoMultiImageResponse(BaseModel):
    """多图智能配置结果"""
    images: list[GeneratedPositionedImage]  # 实际生成的图片列表，按 insertion_index 排序


DocumentStatus = Literal["processing", "ready", "failed"]


# ─── Content Segments (图文混排) ──────────────────────────────────────────────

class TextSegment(BaseModel):
    type: Literal["text"]
    content: str


class ImageSegment(BaseModel):
    type: Literal["image"]
    url: str
    filename: str | None = None
    caption: str | None = None
    insertedBy: Literal["manual", "ai"]
    promptUsed: str | None = None
    contextBefore: str | None = None
    contextAfter: str | None = None


ContentSegment = TextSegment | ImageSegment


class SaveVariantContentRequest(BaseModel):
    segments: list[ContentSegment]


class VariantContentResponse(BaseModel):
    variant_id: int
    segments: list[ContentSegment]
    updated_at: datetime


class GenerateContextualImageRequest(BaseModel):
    variant_id: int
    context_before: str = ""
    context_after: str = ""
    user_prompt: str = ""
    size: str = "1792x1024"


class GenerateContextualImageResponse(BaseModel):
    image_url: str
    filename: str
    prompt_used: str
    caption: str


class ImageUploadResponse(BaseModel):
    """本地文件上传响应"""
    image_url: str
    filename: str


# ─── Knowledge Documents ──────────────────────────────────────────────────────


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
