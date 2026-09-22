from __future__ import annotations

import os

from .base import SYSTEM_PROMPT, LLMProvider, ProviderError


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(self, model: str = "gpt-4o-mini", api_key: str | None = None):
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    def is_available(self) -> bool:
        return bool(self.api_key)

    def review(self, code: str, language: str) -> str:
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY is not set")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError("openai package is not installed") from exc

        client = OpenAI(api_key=self.api_key)
        response = client.chat.completions.create(
            model=self.model,
            temperature=0,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Review this {language} code:\n\n```{language}\n{code}\n```",
                },
            ],
        )
        return response.choices[0].message.content or ""
