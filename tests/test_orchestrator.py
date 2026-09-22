from codesentinel.review.orchestrator import review_source
from codesentinel.rules.engine import RuleConfig


def test_review_source_no_llm(tmp_path):
    src = "def f(x=[]):\n    return x\n"
    config = RuleConfig.load(tmp_path / "none.yml")
    result = review_source(src, language="python", target="t.py", provider=None, rule_config=config)
    assert result.target == "t.py"
    assert any(f.rule_id == "mutable-default-arg" for f in result.findings)
    assert result.llm_summary is None
    assert result.score < 100


def test_clean_code_scores_100(tmp_path):
    src = "def add(a: int, b: int) -> int:\n    return a + b\n"
    config = RuleConfig.load(tmp_path / "none.yml")
    result = review_source(src, language="python", provider=None, rule_config=config)
    assert result.score == 100
    assert result.verdict == "Good"


def test_generic_language_uses_regex_checks(tmp_path):
    src = 'const apiKey = "abcd1234efgh5678";\n'
    config = RuleConfig.load(tmp_path / "none.yml")
    result = review_source(src, language="javascript", provider=None, rule_config=config)
    assert any(f.rule_id == "hardcoded-secret" for f in result.findings)
