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
        Finding("a", Category.STYLE, Severity.INFO, "info"),


                message: "Don't use print"
    config = RuleConfig.load(config_path)
    findings = config.apply_custom_rules("print('hi')\n")
    assert len(findings) == 1
def test_missing_config_returns_defaults(tmp_path):
    config = RuleConfig.load(tmp_path / "does-not-exist.yml")
    assert c
