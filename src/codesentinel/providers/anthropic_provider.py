from __future__ import annotations

import os

from .base import SYSTEM_PROMPT, LLMProvider, ProviderError


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, model: str = "claude-sonnet-5", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def review(self, code: str, language: str) -> str:
        if not self.api_key:
            raise ProviderError("ANTHROPIC_API_KEY is not set")
        try:
            import anthropic
        except ImportError as exc:
            raise ProviderError("anthropic package is not installed") from exc

        client = anthropic.Anthropic(api_key=self.api_key)
        response = client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"Review this {language} code:\n\n```{language}\n{code}\n```",
                }
            ],
        )
        return "".join(block.text for block in response.content if hasattr(block, "text"))
