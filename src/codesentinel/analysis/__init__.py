from __future__ import annotations

from codesentinel.review.models import Finding

from .generic import analyze_generic
from .static_python import analyze_python


def run_static_analysis(source: str, language: str) -> list[Finding]:
    if language.lower() == "python":
        return analyze_python(source)
    return analyze_generic(source, language.lower())


__all__ = ["run_static_analysis", "analyze_python", "analyze_generic"]
