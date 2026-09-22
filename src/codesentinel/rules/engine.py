"""Config-driven rule engine.

Loads a YAML config that can disable built-in rules, override their
severity, and define extra project-specific regex rules. This lets teams
tune the reviewer without touching Python code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from codesentinel.review.models import Category, Finding, Severity

DEFAULT_CONFIG_NAME = ".codesentinel.yml"


@dataclass
class CustomRule:
    rule_id: str
    pattern: re.Pattern
    message: str
    severity: Severity
    category: Category


@dataclass
class RuleConfig:
    disabled_rules: set[str] = field(default_factory=set)
    severity_overrides: dict[str, Severity] = field(default_factory=dict)
    custom_rules: list[CustomRule] = field(default_factory=list)
    min_severity: Severity = Severity.INFO

    @classmethod
    def load(cls, path: str | Path | None = None) -> "RuleConfig":
        candidate = Path(path) if path else Path.cwd() / DEFAULT_CONFIG_NAME
        if not candidate.exists():
            return cls()

        raw: dict[str, Any] = yaml.safe_load(candidate.read_text()) or {}

        disabled = set(raw.get("disable", []) or [])

        overrides: dict[str, Severity] = {}
        for rule_id, sev in (raw.get("severity_overrides", {}) or {}).items():
            overrides[rule_id] = Severity(sev)

        custom_rules: list[CustomRule] = []
        for entry in raw.get("custom_rules", []) or []:
            custom_rules.append(
                CustomRule(
                    rule_id=entry["id"],
                    pattern=re.compile(entry["pattern"]),
                    message=entry["message"],
                    severity=Severity(entry.get("severity", "medium")),
                    category=Category(entry.get("category", "maintainability")),
                )
            )

        min_severity = Severity(raw.get("min_severity", "info"))

        return cls(
            disabled_rules=disabled,
            severity_overrides=overrides,
            custom_rules=custom_rules,
            min_severity=min_severity,
        )

    def apply_custom_rules(self, source: str) -> list[Finding]:
        findings: list[Finding] = []
        for rule in self.custom_rules:
            for lineno, line in enumerate(source.splitlines(), start=1):
                if rule.pattern.search(line):
                    findings.append(
                        Finding(
                            rule_id=rule.rule_id,
                            category=rule.category,
                            severity=rule.severity,
                            message=rule.message,
                            line=lineno,
                        )
                    )
        return findings

    def filter_and_adjust(self, findings: list[Finding]) -> list[Finding]:
        result: list[Finding] = []
        for f in findings:
            if f.rule_id in self.disabled_rules:
                continue
            if f.rule_id in self.severity_overrides:
                f.severity = self.severity_overrides[f.rule_id]
            if f.severity.weight < self.min_severity.weight:
                continue
            result.append(f)
        return result
