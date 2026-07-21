from openai import OpenAI


class LLMClient:
    """Thin wrapper around any OpenAI-compatible chat completions endpoint.

    Vendor/model are fully determined by the base_url/api_key/model passed in —
    swapping providers (OpenAI, DeepSeek, Azure OpenAI, local vLLM/Ollama, ...)
    requires no code change, only different construction args.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.8,
        timeout: float = 60.0,
    ):
        self._client = OpenAI(base_url=base_url, api_key=api_key, timeout=timeout)
        self.model = model
        self.temperature = temperature

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> str:
        """Single-turn chat completion. Returns raw text content."""
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature if temperature is not None else self.temperature,
        )
        return resp.choices[0].message.content or ""


def get_llm_client() -> LLMClient:
    from app.config import settings

    return LLMClient(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        timeout=settings.llm_request_timeout,
    )
