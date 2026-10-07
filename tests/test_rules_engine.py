import textwrap

from codesentinel.rules.engine import RuleConfig
from codesentinel.review.models import Category, Finding, Severity


def test_disabled_rule_is_filtered(tmp_path):
    config_path = tmp_path / ".codesentinel.yml"
    config_path.write_text("disable:\n  - unused-import\n")
    config = RuleConfig.load(config_path)

    findings = [
        Finding("unused-import", Category.STYLE, Severity.INFO, "unused"),
        Finding("bare-except", Category.BUG, Severity.MEDIUM, "bare except"),
    ]
    result = config.filter_and_adjust(findings)
    assert [f.rule_id for f in result] == ["bare-except"]


def test_severity_override(tmp_path):
    config_path = tmp_path / ".codesentinel.yml"
    config_path.write_text("severity_overrides:\n  bare-except: critical\n")
    config = RuleConfig.load(config_path)

    findings = [Finding("bare-except", Category.BUG, Severity.MEDIUM, "bare except")]
    result = config.filter_and_adjust(findings)
    assert result[0].severity == Severity.CRITICAL


def test_min_severity_filters_low_findings(tmp_path):
    config_path = tmp_path / ".codesentinel.yml"
    config_path.write_text("min_severity: high\n")
    config = RuleConfig.load(config_path)

    findings = [
        Finding("a", Category.STYLE, Severity.INFO, "info"),
        Finding("b", Category.SECURITY, Severity.CRITICAL, "critical"),
    ]
    result = config.filter_and_adjust(findings)
    assert [f.rule_id for f in result] == ["b"]


def test_custom_rule_matches_source(tmp_path):
    config_path = tmp_path / ".codesentinel.yml"
    config_path.write_text(
        textwrap.dedent(
            """
            custom_rules:
              - id: no-print
                pattern: '\\bprint\\('
                message: "Don't use print"
                severity: low
                category: style
            """
        )
    )
    config = RuleConfig.load(config_path)
    findings = config.apply_custom_rules("print('hi')\n")
    assert len(findings) == 1
    assert findings[0].rule_id == "no-print"


def test_missing_config_returns_defaults(tmp_path):
    config = RuleConfig.load(tmp_path / "does-not-exist.yml")
    assert config.disabled_rules == set()
    assert config.custom_rules == []
