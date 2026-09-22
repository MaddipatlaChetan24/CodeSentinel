"""Provider-agnostic interface for LLM-backed review."""

from __future__ import annotations

from abc import ABC, abstractmethod

SYSTEM_PROMPT = """You are an expert code reviewer. Analyze the provided code and \
return concise, high-signal observations that a static analyzer would miss: \
design issues, unclear intent, risky assumptions, and missing edge-case handling.

Do not repeat generic style nitpicks (formatting, naming) — a linter already \
handles those. Focus on correctness, security, and architecture.

Respond in plain markdown prose, organized under short headings. Keep it under \
300 words."""


class LLMProvider(ABC):
    """Base class every LLM backend must implement."""

    name: str = "base"

    @abstractmethod
    def review(self, code: str, language: str) -> str:
        """Return a markdown narrative review of the given code."""
        raise NotImplementedError

    def is_available(self) -> bool:
        return True


class ProviderError(RuntimeError):
    pass
