"""Pluggable LLM provider registry."""

from __future__ import annotations

from .anthropic_provider import AnthropicProvider
from .base import LLMProvider, ProviderError
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider

_REGISTRY: dict[str, type[LLMProvider]] = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "ollama": OllamaProvider,
}


def get_provider(name: str, **kwargs) -> LLMProvider:
    try:
        cls = _REGISTRY[name]
    except KeyError as exc:
        raise ValueError(
            f"Unknown provider '{name}'. Available: {', '.join(_REGISTRY)}"
        ) from exc
    return cls(**kwargs)


def first_available(order: list[str] | None = None) -> LLMProvider | None:
    """Return the first provider in `order` that is actually usable."""
    order = order or ["anthropic", "openai", "ollama"]
    for name in order:
        provider = get_provider(name)
        if provider.is_available():
            return provider
    return None


__all__ = [
    "LLMProvider",
    "ProviderError",
    "OpenAIProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "get_provider",
    "first_available",
]
