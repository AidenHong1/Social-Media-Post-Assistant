import json
import uuid
from pathlib import Path

import httpx

from app.config import settings


class ImageService:
    def _api_key(self) -> str:
        return settings.image_api_key or settings.llm_api_key

    def _image_dir(self) -> Path:
        p = Path(settings.image_storage_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

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

        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{settings.image_api_base_url}/images/generations",
                headers=headers,
                json=payload,
            )
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

            return f"/api/images/files/{filename}", filename

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
