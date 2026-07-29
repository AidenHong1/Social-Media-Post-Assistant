import asyncio
import json
import logging
import time
import uuid
from pathlib import Path

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self):
        self._last_request_time = 0
        self._min_request_interval = settings.image_rate_limit_interval

    def _api_key(self) -> str:
        return settings.image_api_key or settings.llm_api_key

    def _image_dir(self) -> Path:
        p = Path(settings.image_storage_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

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
  "image_prompt": "detailed English DALL-E 3 prompt, describe scene/style/mood",
  "insertion_position": "after_hook",
  "caption": "short caption under 15 words"
}}

insertion_position must be one of: beginning, after_hook, before_cta, end"""

        headers = {
            "Authorization": f"Bearer {self._api_key()}",
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

    async def generate_image(self, prompt: str, size: str = "1024x1024") -> tuple[str, str]:
        """Generate image via DALL-E 3 compatible API, download and save locally.

        Returns: (image_url, filename)
        """
        max_retries = settings.image_max_retries
        base_delay = 2.0  # 基础延迟（秒）

        headers = {
            "Authorization": f"Bearer {self._api_key()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.image_model,
            "prompt": prompt,
            "n": 1,
            "size": size,
        }

        for attempt in range(max_retries):
            try:
                # 应用速率限制
                await self._rate_limit()

                async with httpx.AsyncClient(timeout=90.0) as client:
                    resp = await client.post(
                        f"{settings.image_api_base_url}/images/generations",
                        headers=headers,
                        json=payload,
                    )

                    # 如果是 429 错误，尝试重试
                    if resp.status_code == 429:
                        if attempt < max_retries - 1:
                            # 计算指数退避延迟
                            retry_after = resp.headers.get("Retry-After")
                            if retry_after and retry_after.isdigit():
                                wait_time = int(retry_after)
                            else:
                                wait_time = base_delay * (2 ** attempt)

                            logger.warning(
                                f"收到 429 错误，第 {attempt + 1}/{max_retries} 次尝试，"
                                f"等待 {wait_time} 秒后重试..."
                            )
                            await asyncio.sleep(wait_time)
                            continue
                        else:
                            # 最后一次尝试也失败了
                            logger.error(
                                f"图片生成失败: API 请求过多 (429)，已重试 {max_retries} 次。"
                                "建议: 1) 减少请求频率 2) 检查 API 配额 3) 稍后再试"
                            )
                            raise httpx.HTTPStatusError(
                                f"API 请求限制: 已达到速率限制，重试 {max_retries} 次后仍失败。"
                                "请稍后再试或联系 API 提供商检查配额。",
                                request=resp.request,
                                response=resp
                            )

                    # 其他 HTTP 错误直接抛出
                    resp.raise_for_status()

                    data = resp.json()
                    remote_url = data["data"][0]["url"]

                    # Download image
                    img_resp = await client.get(remote_url, timeout=60.0)
                    img_resp.raise_for_status()

                    # Save locally
                    filename = f"{uuid.uuid4().hex}.png"
                    filepath = self._image_dir() / filename
                    filepath.write_bytes(img_resp.content)

                    logger.info(f"图片生成成功: {filename}")
                    return f"/api/images/files/{filename}", filename

            except httpx.HTTPStatusError as e:
                if e.response.status_code != 429:
                    # 非 429 错误直接抛出
                    logger.error(f"HTTP 错误: {e}")
                    raise
                # 429 错误会在上面的逻辑中处理
                if attempt == max_retries - 1:
                    raise
            except Exception as e:
                logger.error(f"图片生成失败 (第 {attempt + 1}/{max_retries} 次): {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(base_delay * (2 ** attempt))

    async def auto_for_variant(self, variant_text: str, platform: str) -> dict:
        """Full pipeline: analyze variant → generate image → return complete response."""
        analysis = await self.analyze_variant_for_image(variant_text, platform)

        image_url, filename = await self.generate_image(
            prompt=analysis["image_prompt"],
            size="1024x1024"
        )

        return {
            "image_url": image_url,
            "insertion_position": analysis["insertion_position"],
            "prompt_used": analysis["image_prompt"],
            "caption": analysis["caption"],
            "filename": filename,
        }


image_service = ImageService()
