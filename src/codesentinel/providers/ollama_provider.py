from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from .base import SYSTEM_PROMPT, LLMProvider, ProviderError


class OllamaProvider(LLMProvider):
    """Talks to a locally running Ollama server — no API key required."""

    name = "ollama"

    def __init__(self, model: str | None = None, host: str | None = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.1")
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def is_available(self) -> bool:
        try:
            urllib.request.urlopen(f"{self.host}/api/tags", timeout=1)
            return True
        except (urllib.error.URLError, OSError):
            return False

    def review(self, code: str, language: str) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Review this {language} code:\n\n```{language}\n{code}\n```",
                },
            ],
        }
        req = urllib.request.Request(
            f"{self.host}/api/chat",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode(errors="replace")
            raise ProviderError(f"Ollama returned {exc.code}: {body}") from exc
        except (urllib.error.URLError, OSError) as exc:
            raise ProviderError(f"Could not reach Ollama at {self.host}: {exc}") from exc
        return data.get("message", {}).get("content", "")
