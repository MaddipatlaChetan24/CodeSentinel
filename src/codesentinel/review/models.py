"""Shared data model for review findings and results."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @property
    def weight(self) -> int:
        return {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }[self]


class Category(str, Enum):
    BUG = "bug"
    SECURITY = "security"
    PERFORMANCE = "performance"
    STYLE = "style"
    COMPLEXITY = "complexity"
    MAINTAINABILITY = "maintainability"
    LLM_INSIGHT = "llm_insight"


@dataclass
class Finding:
    rule_id: str
    category: Category
    severity: Severity
    message: str
    line: int | None = None
    column: int | None = None
    source: str = "static"  # "static" or the LLM provider name
    suggestion: str | None = None

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "line": self.line,
            "column": self.column,
            "source": self.source,
            "suggestion": self.suggestion,
        }


@dataclass
class ReviewResult:
    target: str
    language: str
    findings: list[Finding] = field(default_factory=list)
    llm_summary: str | None = None
    llm_provider: str | None = None
    duration_seconds: float = 0.0
    created_at: float = field(default_factory=time.time)

    @property
    def score(self) -> int:
        """0-100 quality score derived from weighted severity penalties."""
        if not self.findings:
            return 100
        penalty = sum(f.severity.weight * 5 for f in self.findings)
        return max(0, 100 - penalty)

    @property
    def verdict(self) -> str:
        s = self.score
        if s >= 85:
            return "Good"
        if s >= 60:
            return "Needs Work"
        return "Critical Issues"

    def counts_by_severity(self) -> dict[str, int]:
        out = {sev.value: 0 for sev in Severity}
        for f in self.findings:
            out[f.severity.value] += 1
        return out

    def to_dict(self) -> dict:
        return {
            "target": self.target,
            "language": self.language,
            "score": self.score,
            "verdict": self.verdict,
            "findings": [f.to_dict() for f in self.findings],
            "counts_by_severity": self.counts_by_severity(),
            "llm_summary": self.llm_summary,
            "llm_provider": self.llm_provider,
            "duration_seconds": round(self.duration_seconds, 3),
            "created_at": self.created_at,
        }
