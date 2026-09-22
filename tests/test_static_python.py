from codesentinel.analysis.static_python import analyze_python


def _rule_ids(source: str) -> set[str]:
    return {f.rule_id for f in analyze_python(source)}


def test_bare_except_detected():
    src = "try:\n    pass\nexcept:\n    pass\n"
    assert "bare-except" in _rule_ids(src)


def test_mutable_default_detected():
    src = "def f(x=[]):\n    return x\n"
    assert "mutable-default-arg" in _rule_ids(src)


def test_eval_detected():
    src = "def f(x):\n    return eval(x)\n"
    ids = _rule_ids(src)
    assert "dangerous-eval-exec" in ids


def test_shell_true_detected():
    src = "import subprocess\nsubprocess.run(cmd, shell=True)\n"
    assert "subprocess-shell-true" in _rule_ids(src)


def test_hardcoded_secret_detected():
    src = 'api_key = "sk-1234567890abcdef"\n'
    assert "hardcoded-secret" in _rule_ids(src)


def test_unused_import_detected():
    src = "import os\nimport sys\nprint(sys.argv)\n"
    assert "unused-import" in _rule_ids(src)


def test_clean_code_has_no_bug_findings():
    src = "def add(a: int, b: int) -> int:\n    return a + b\n"
    findings = analyze_python(src)
    assert findings == []


def test_syntax_error_reported():
    src = "def f(:\n"
    findings = analyze_python(src)
    assert len(findings) == 1
    assert findings[0].rule_id == "syntax-error"


def test_high_complexity_detected():
    branches = "\n".join(f"    if x == {i}:\n        y += 1" for i in range(15))
    src = f"def f(x):\n    y = 0\n{branches}\n    return y\n"
    assert "high-cyclomatic-complexity" in _rule_ids(src)
