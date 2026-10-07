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
    config_path = tmp_path / ".codesentinel.yml"
    config = RuleConfig.load(config_path)

    findings = [Finding("bare-except", Category.BUG, Severity.MEDIUM, 
        Finding("a", Category.STYLE, Severity.INFO, "info"),
        Finding("b", Category.SECURITY, Severity.CRITICAL, "critical"),
    ]


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
