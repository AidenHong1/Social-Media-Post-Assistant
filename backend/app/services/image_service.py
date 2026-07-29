import asyncio
import json
import logging
import re
import time
import uuid
from pathlib import Path

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
}
MAX_IMAGE_UPLOAD_MB = 10


class UnsupportedImageTypeError(Exception):
    pass


class ImageTooLargeError(Exception):
    pass


class ImageService:
    def __init__(self):
        self._last_request_time = 0
        self._min_request_interval = settings.image_rate_limit_interval

    def _llm_api_key(self) -> str:
        return settings.llm_api_key

    def _image_api_key(self) -> str:
        return settings.image_api_key

    def _image_dir(self) -> Path:
        p = Path(settings.image_storage_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _normalize_image_prompt(self, prompt: object) -> str:
        """Normalize image prompt into a compact single-line string accepted by image APIs."""
        if isinstance(prompt, str):
            text = prompt
        elif prompt is None:
            text = ""
        else:
            text = json.dumps(prompt, ensure_ascii=False)

        text = text.replace("```", " ").replace("\r", " ").replace("\n", " ")
        text = " ".join(text.split()).strip()
        # Keep prompt compact to reduce provider-side validation failures.
        return text[:600]

    async def _rate_limit(self):
        """确保请求之间有最小间隔"""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._min_request_interval:
            wait_time = self._min_request_interval - elapsed
            logger.info(f"速率限制: 等待 {wait_time:.2f} 秒")
            await asyncio.sleep(wait_time)
        self._last_request_time = time.time()

    async def analyze_variant_for_image(self, variant_text: str, platform: str) -> dict:
        """Call LLM to suggest DALL-E prompt and insertion position for a variant."""
        system = (
            "You are a social media visual director. "
            "Always respond with valid JSON only, no markdown."
        )
        user = f"""Analyze this {platform} post and suggest the best accompanying image.

Post:
{variant_text}

Return JSON:
{{
  "image_prompt": "concise English image prompt under 600 characters, focus on subject/style/composition",
  "insertion_position": "after_hook",
  "caption": "short caption under 15 words"
}}

insertion_position must be one of: beginning, after_hook, before_cta, end"""

        headers = {
            "Authorization": f"Bearer {self._llm_api_key()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.6,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        return json.loads(content)

    async def _download_and_save_image(self, url: str) -> tuple[str, str]:
        """下载图片并保存到本地"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            img_resp = await client.get(url)
            img_resp.raise_for_status()

            filename = f"{uuid.uuid4().hex}.png"
            filepath = self._image_dir() / filename
            filepath.write_bytes(img_resp.content)

            logger.info(f"图片下载并保存成功: {filename} ({len(img_resp.content)} 字节)")
            return f"/api/images/files/{filename}", filename

    def save_uploaded_image(self, filename: str, content_type: str | None, content: bytes) -> tuple[str, str]:
        """校验并保存本地上传的图片文件到磁盘。

        Returns: (image_url, filename)
        """
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise UnsupportedImageTypeError(f"不支持的图片格式: .{ext}")
        if content_type and content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise UnsupportedImageTypeError(f"不支持的文件类型: {content_type}")

        max_bytes = MAX_IMAGE_UPLOAD_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise ImageTooLargeError(f"图片大小超过 {MAX_IMAGE_UPLOAD_MB}MB 限制")

        saved_filename = f"{uuid.uuid4().hex}.{ext}"
        filepath = self._image_dir() / saved_filename
        filepath.write_bytes(content)

        logger.info(f"本地图片上传成功: {saved_filename} ({len(content)} 字节)")
        return f"/api/images/files/{saved_filename}", saved_filename

    async def generate_image(self, prompt: str, size: str = "1792x1024") -> tuple[str, str]:
        """Generate image via Aliyun DashScope z-image-turbo.

        Returns: (image_url, filename)
        """
        max_retries = settings.image_max_retries
        base_delay = 2.0
        generation_timeout = 180.0

        # Z-Image-Turbo expects width*height strings.
        size_mapping = {
            "1024x1024": "1024*1024",
            "1024x1792": "720*1280",
            "1792x1024": "1280*720",
        }
        aliyun_size = size_mapping.get(size, "1024*1024")
        normalized_prompt = self._normalize_image_prompt(prompt)

        if not normalized_prompt:
            raise HTTPException(status_code=400, detail="图片生成提示词为空，无法调用图片模型")

        headers = {
            "Authorization": f"Bearer {self._image_api_key()}",
            "Content-Type": "application/json",
        }

        # z-image-turbo uses the multimodal-generation API with a single user message.
        payload = {
            "model": settings.image_model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": normalized_prompt}],
                    }
                ]
            },
            "parameters": {
                "size": aliyun_size,
                "prompt_extend": False,
            },
        }

        for attempt in range(max_retries):
            try:
                await self._rate_limit()
                logger.info(f"开始生成图片 (尝试 {attempt + 1}/{max_retries})")

                async with httpx.AsyncClient(timeout=generation_timeout) as client:
                    resp = await client.post(
                        f"{settings.image_api_base_url}/services/aigc/multimodal-generation/generation",
                        headers=headers,
                        json=payload,
                    )

                    if resp.status_code == 429:
                        if attempt < max_retries - 1:
                            retry_after = resp.headers.get("Retry-After")
                            wait_time = int(retry_after) if retry_after and retry_after.isdigit() else base_delay * (2 ** attempt)
                            logger.warning(f"收到 429 错误，等待 {wait_time} 秒后重试...")
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            raise HTTPException(status_code=429, detail="API 请求限制: 已达到速率限制。")

                    resp.raise_for_status()
                    result = resp.json()

                    if result.get("code"):
                        logger.error(f"API 错误: {result.get('message')}")
                        raise HTTPException(
                            status_code=500,
                            detail=f"图片生成失败: {result.get('message', 'Unknown error')}"
                        )

                    choices = result.get("output", {}).get("choices", [])
                    if not choices:
                        logger.error(f"意外的响应格式: {result}")
                        raise HTTPException(status_code=500, detail="API 返回了意外的响应格式")

                    content_items = choices[0].get("message", {}).get("content", [])
                    remote_url = next(
                        (
                            item.get("image")
                            for item in content_items
                            if isinstance(item, dict) and item.get("image")
                        ),
                        None,
                    )

                    if not remote_url:
                        logger.error(f"API 返回结果中没有图片 URL: {result}")
                        raise HTTPException(status_code=500, detail="API 返回结果中没有图片 URL")

                    logger.info(f"图片生成成功，开始下载: {remote_url[:100]}...")
                    return await self._download_and_save_image(remote_url)

            except httpx.ReadTimeout:
                logger.error(f"请求超时 (第 {attempt + 1}/{max_retries} 次)")
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise HTTPException(
                        status_code=504,
                        detail=f"图片生成超时: API 响应时间过长。已重试 {max_retries} 次。"
                    )

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    if attempt == max_retries - 1:
                        raise HTTPException(status_code=429, detail="API 请求限制: 速率限制。")
                else:
                    response_text = e.response.text
                    logger.error(f"HTTP 错误 {e.response.status_code}: {response_text}")
                    raise HTTPException(
                        status_code=e.response.status_code,
                        detail=f"API 错误: {response_text or str(e)}"
                    )

            except HTTPException:
                raise

            except Exception as e:
                logger.error(f"图片生成失败 (第 {attempt + 1}/{max_retries} 次): {type(e).__name__}: {e}")
                if attempt == max_retries - 1:
                    raise HTTPException(status_code=500, detail=f"图片生成失败: {type(e).__name__}: {str(e)}")
                await asyncio.sleep(base_delay * (2 ** attempt))

        raise HTTPException(status_code=500, detail="图片生成失败: 未知错误")

    async def _build_contextual_prompt(self, context_before: str, context_after: str, user_prompt: str) -> tuple[str, str]:
        """结合上下文与用户提示词，让 LLM 生成匹配插入位置的图片提示词和简短说明。

        Returns: (image_prompt, caption)
        """
        context_before = (context_before or "").strip()
        context_after = (context_after or "").strip()
        user_prompt = (user_prompt or "").strip()

        if not context_before and not context_after and not user_prompt:
            raise HTTPException(status_code=400, detail="缺少上下文或提示词，无法智能生成图片")

        system = (
            "You are a social media visual director. "
            "Always respond with valid JSON only, no markdown."
        )
        user = f"""Based on the surrounding text of an insertion point in a social media post, "
suggest an accompanying image that fits naturally at this exact position.

Text immediately BEFORE the insertion point:
{context_before or "(none)"}

Text immediately AFTER the insertion point:
{context_after or "(none)"}

User's manual hint for the image (may be empty, but if present it MUST take priority and be reflected in the prompt):
{user_prompt or "(none)"}

Return JSON:
{{
  "image_prompt": "concise English image prompt under 600 characters, focus on subject/style/composition, consistent with the surrounding text and the user's hint",
  "caption": "short caption under 15 words"
}}"""

        headers = {
            "Authorization": f"Bearer {self._llm_api_key()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.6,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        data = json.loads(content)

        image_prompt = data.get("image_prompt", "").strip()
        caption = data.get("caption", "").strip()

        if user_prompt:
            image_prompt = f"{image_prompt}. {user_prompt}" if image_prompt else user_prompt

        return image_prompt, caption

    async def generate_contextual_image(
        self,
        context_before: str,
        context_after: str,
        user_prompt: str,
        size: str = "1792x1024",
    ) -> dict:
        """根据插入位置上下文（前后文本 + 可选用户提示词）智能生成匹配的图片。"""
        image_prompt, caption = await self._build_contextual_prompt(context_before, context_after, user_prompt)
        prompt_used = self._normalize_image_prompt(image_prompt)

        image_url, filename = await self.generate_image(prompt=prompt_used, size=size)

        return {
            "image_url": image_url,
            "filename": filename,
            "prompt_used": prompt_used,
            "caption": caption,
        }

    async def auto_for_variant(self, variant_text: str, platform: str) -> dict:
        """Full pipeline: analyze variant → generate image → return complete response."""
        analysis = await self.analyze_variant_for_image(variant_text, platform)
        prompt_used = self._normalize_image_prompt(analysis.get("image_prompt"))

        image_url, filename = await self.generate_image(
            prompt=prompt_used,
            size="1792x1024"
        )

        return {
            "image_url": image_url,
            "insertion_position": analysis["insertion_position"],
            "prompt_used": prompt_used,
            "caption": analysis["caption"],
            "filename": filename,
        }

    async def analyze_multi_positions_for_variant(
        self, variant_text: str, platform: str, max_images: int = 3
    ) -> list[dict]:
        """分析文案结构，返回多个插入位置及对应的图片 prompt 建议。

        Returns: list of {"insertion_index": int, "image_prompt": str, "caption": str}
        """
        # 先按段落拆分（与前端一致的逻辑）
        paragraphs = [p.strip() for p in re.split(r'\n\n+', variant_text) if p.strip()]
        total_paragraphs = len(paragraphs)

        # 构造完整的段落索引信息给 LLM
        paragraphs_text = "\n\n".join([f"[段落 {i}]: {p}" for i, p in enumerate(paragraphs)])

        system = (
            "You are a social media visual director optimizing post engagement. "
            "Always respond with valid JSON only, no markdown."
        )
        user = f"""Analyze this {platform} post and suggest the best positions to insert images for maximum engagement.

Post has {total_paragraphs} paragraphs:

{paragraphs_text}

Your task:
1. Identify {max_images} optimal insertion points (segment indices where images should be inserted)
2. For each position, generate a concise English DALL-E prompt that matches the surrounding context
3. Provide a short caption for each image

Rules:
- insertion_index: integer from 0 to {total_paragraphs} (0=before first paragraph, {total_paragraphs}=after last)
- Distribute images evenly to maintain visual flow (avoid clustering)
- Each image_prompt must be contextually relevant to nearby paragraphs
- Prioritize hook (early) and CTA/conclusion positions for higher engagement

Return JSON array (exactly {max_images} items):
[
  {{
    "insertion_index": 1,
    "image_prompt": "concise English prompt under 500 chars",
    "caption": "short caption under 15 words"
  }},
  ...
]"""

        headers = {
            "Authorization": f"Bearer {self._llm_api_key()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.llm_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.6,
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.llm_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()

        content = resp.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        suggestions = json.loads(content)
        if not isinstance(suggestions, list):
            raise ValueError(f"Expected JSON array, got: {type(suggestions)}")

        return suggestions[:max_images]  # 防止 LLM 返回超过 max_images 个

    async def auto_multi_for_variant(
        self, variant_text: str, platform: str, max_images: int = 3
    ) -> dict:
        """多图智能配置完整流程：分析多个位置 → 为每个位置生成图片。

        Returns: {
            "suggestions": [...],  # 原始建议列表
            "images": [...]        # 实际生成的图片列表
        }
        """
        suggestions = await self.analyze_multi_positions_for_variant(
            variant_text, platform, max_images
        )

        images = []
        for suggestion in suggestions:
            prompt_used = self._normalize_image_prompt(suggestion["image_prompt"])

            try:
                image_url, filename = await self.generate_image(
                    prompt=prompt_used,
                    size="1792x1024"
                )

                images.append({
                    "image_url": image_url,
                    "insertion_index": int(suggestion["insertion_index"]),
                    "prompt_used": prompt_used,
                    "caption": suggestion["caption"],
                    "filename": filename,
                })
            except Exception as e:
                logger.error(f"Failed to generate image for position {suggestion['insertion_index']}: {e}")
                # 跳过失败的图片，继续生成其他图片
                continue

        # 按 insertion_index 升序排列，便于前端从后往前依次插入（避免索引偏移）
        images.sort(key=lambda img: img["insertion_index"])

        return {"images": images}


image_service = ImageService()
