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


