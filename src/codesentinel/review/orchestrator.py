"""Combines static analysis, the rule engine, and an optional LLM pass into
a single ReviewResult.
"""

from __future__ import annotations

import time

from codesentinel.analysis import run_static_analysis
from codesentinel.providers.base import LLMProvider, ProviderError
from codesentinel.rules import RuleConfig

from .models import ReviewResult


def review_source(
    source: str,
    language: str = "python",
    target: str = "<inline>",
    provider: LLMProvider | None = None,
    rule_config: RuleConfig | None = None,
) -> ReviewResult:
    start = time.monotonic()
    rule_config = rule_config or RuleConfig.load()

    findings = run_static_analysis(source, language)
    findings.extend(rule_config.apply_custom_rules(source))
    findings = rule_config.filter_and_adjust(findings)
    findings.sort(key=lambda f: (-f.severity.weight, f.line or 0))

    result = ReviewResult(target=target, language=language, findings=findings)

    if provider is not None:
        try:
            if provider.is_available():
                result.llm_summary = provider.review(source, language)
                result.llm_provider = provider.name
            else:
                result.llm_summary = (
                    f"({provider.name} provider not configured — set the "
                    "required API key/host to enable LLM insights.)"
                )
        except ProviderError as exc:
            result.llm_summary = f"(LLM review skipped: {exc})"

    result.duration_seconds = time.monotonic() - start
    return result
