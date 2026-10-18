"""Lightweight regex-based checks that apply to any text-based source file.

These run for languages that don't have a dedicated AST analyzer yet
(JS, Go, Java, ...) so the tool never falls back to LLM-only review.
"""

from __future__ import annotations

import re

from codesentinel.review.models import Category, Finding, Severity

_SECRET_PATTERN = re.compile(
    r"(?i)\b(api[_-]?key|secret|password|passwd|token|access[_-]?key)\b\s*[:=]\s*['\"][^'\"]{4,}['\"]"
)
_TODO_PATTERN = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
_CONSOLE_DEBUG = re.compile(r"\bconsole\.(log|debug)\s*\(")
_SQL_CONCAT = re.compile(
    r"(?i)(select|insert|update|delete)\b.{0,80}?\+\s*[a-zA-Z_]\w*"
)


def analyze_generic(source: str, language: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = source.splitlines()

    for lineno, line in enumerate(lines, start=1):
        if _SECRET_PATTERN.search(line):
            findings.append(
                Finding(
                    rule_id="hardcoded-secret",
                    category=Category.SECURITY,
                    severity=Severity.CRITICAL,
                    message="Possible hardcoded credential or secret.",
                    line=lineno,
                )
            )
        if _SQL_CONCAT.search(line):
            findings.append(
                Finding(
                    rule_id="sql-string-concatenation",
                    category=Category.SECURITY,
                    severity=Severity.HIGH,
                    message="SQL query appears to be built with string "
                    "concatenation. Use parameterized queries to avoid "
                    "SQL injection.",
                    line=lineno,
                )
            )
        if language in ("javascript", "typescript") and _CONSOLE_DEBUG.search(line):
            findings.append(
                Finding(
                    rule_id="leftover-console-debug",
                    category=Category.STYLE,
                    severity=Severity.INFO,
                    message="Leftover console.log/debug statement.",
                    line=lineno,
                )
            )
        if _TODO_PATTERN.search(line):
            findings.append(
                Finding(
                    rule_id="todo-comment",
                    category=Category.MAINTAINABILITY,
                    severity=Severity.INFO,
                    message="Unresolved TODO/FIXME comment.",
                    line=lineno,
                )
            )
        if len(line) > 120:
            findings.append(
                Finding(
                    rule_id="line-too-long",
                    category=Category.STYLE,
                    severity=Severity.INFO,
                    message=f"Line is {len(line)} characters long (limit 120).",
                    line=lineno,
                )
            )

    return findings
