"""AST-based static analysis for Python — bugs, security, and maintainability
checks that don't depend on an LLM call.
"""

from __future__ import annotations

import ast
import re

from codesentinel.review.models import Category, Finding, Severity

_SECRET_PATTERN = re.compile(
    r"(?i)\b(api_key|apikey|secret|password|passwd|token|access_key)\b\s*=\s*['\"][^'\"]{4,}['\"]"
)

_SHELL_INJECTION_FUNCS = {"os.system", "os.popen"}
_UNSAFE_DESERIALIZERS = {"pickle.load", "pickle.loads", "yaml.load"}


def _dotted_name(node: ast.AST) -> str | None:
    """Best-effort reconstruction of `a.b.c` from an Attribute/Call node."""
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


class _Analyzer(ast.NodeVisitor):
    def __init__(self, source: str):
        self.source = source
        self.lines = source.splitlines()
        self.findings: list[Finding] = []
        self._imported_names: dict[str, int] = {}
        self._used_names: set[str] = set()

    # ---- bugs & correctness -------------------------------------------------

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self.findings.append(
                Finding(
                    rule_id="bare-except",
                    category=Category.BUG,
                    severity=Severity.MEDIUM,
                    message="Bare `except:` swallows all exceptions, including "
                    "KeyboardInterrupt/SystemExit. Catch a specific exception type.",
                    line=node.lineno,
                )
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_mutable_defaults(node)
        self._check_complexity(node)
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def _check_mutable_defaults(self, node: ast.FunctionDef) -> None:
        for default in [*node.args.defaults, *node.args.kw_defaults]:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self.findings.append(
                    Finding(
                        rule_id="mutable-default-arg",
                        category=Category.BUG,
                        severity=Severity.HIGH,
                        message=f"Function `{node.name}` uses a mutable default "
                        "argument. It is shared across all calls and can leak "
                        "state between invocations. Use `None` and initialize "
                        "inside the function body.",
                        line=node.lineno,
                    )
                )

    def _check_complexity(self, node: ast.FunctionDef) -> None:
        complexity = 1
        for child in ast.walk(node):
            if isinstance(
                child,
                (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.BoolOp),
            ):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        if complexity > 10:
            self.findings.append(
                Finding(
                    rule_id="high-cyclomatic-complexity",
                    category=Category.COMPLEXITY,
                    severity=Severity.MEDIUM if complexity <= 15 else Severity.HIGH,
                    message=f"Function `{node.name}` has an estimated cyclomatic "
                    f"complexity of {complexity}. Consider splitting it into "
                    "smaller functions.",
                    line=node.lineno,
                )
            )

    def visit_Compare(self, node: ast.Compare) -> None:
        for op, comparator in zip(node.ops, node.comparators):
            if isinstance(op, (ast.Is, ast.IsNot)) and isinstance(
                comparator, (ast.Constant,)
            ) and not isinstance(comparator.value, (bool, type(None))):
                self.findings.append(
                    Finding(
                        rule_id="is-comparison-with-literal",
                        category=Category.BUG,
                        severity=Severity.MEDIUM,
                        message="Using `is`/`is not` to compare with a literal "
                        "value relies on interning and can give wrong results. "
                        "Use `==`/`!=` instead.",
                        line=node.lineno,
                    )
                )
        self.generic_visit(node)

    # ---- security -------------------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        callee = _dotted_name(node.func)

        if callee in ("eval", "exec"):
            self.findings.append(
                Finding(
                    rule_id="dangerous-eval-exec",
                    category=Category.SECURITY,
                    severity=Severity.CRITICAL,
                    message=f"`{callee}()` executes arbitrary code. If input can "
                    "reach this call, it is a remote code execution risk.",
                    line=node.lineno,
                )
            )

        if callee in _SHELL_INJECTION_FUNCS:
            self.findings.append(
                Finding(
                    rule_id="shell-injection-risk",
                    category=Category.SECURITY,
                    severity=Severity.HIGH,
                    message=f"`{callee}()` runs a shell command. If any part of "
                    "the command is built from untrusted input, this is a shell "
                    "injection vector. Prefer `subprocess.run([...], shell=False)`.",
                    line=node.lineno,
                )
            )

        if callee == "subprocess.run" or callee == "subprocess.Popen" or callee == "subprocess.call":
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self.findings.append(
                        Finding(
                            rule_id="subprocess-shell-true",
                            category=Category.SECURITY,
                            severity=Severity.HIGH,
                            message=f"`{callee}(..., shell=True)` opens a shell "
                            "injection risk when arguments include untrusted "
                            "data. Pass a list of args with `shell=False` instead.",
                            line=node.lineno,
                        )
                    )

        if callee in _UNSAFE_DESERIALIZERS:
            self.findings.append(
                Finding(
                    rule_id="unsafe-deserialization",
                    category=Category.SECURITY,
                    severity=Severity.HIGH,
                    message=f"`{callee}()` can execute arbitrary code when "
                    "deserializing untrusted data. Use `json` or "
                    "`yaml.safe_load` instead.",
                    line=node.lineno,
                )
            )

        if callee == "hashlib.md5" or callee == "hashlib.sha1":
            self.findings.append(
                Finding(
                    rule_id="weak-hash-algorithm",
                    category=Category.SECURITY,
                    severity=Severity.LOW,
                    message=f"`{callee}()` is cryptographically weak. Use "
                    "`hashlib.sha256` or better for anything security-sensitive.",
                    line=node.lineno,
                )
            )

        self.generic_visit(node)

    # ---- style / hygiene --------------------------------------------------

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._imported_names[alias.asname or alias.name.split(".")[0]] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            if alias.name == "*":
                self.findings.append(
                    Finding(
                        rule_id="wildcard-import",
                        category=Category.STYLE,
                        severity=Severity.LOW,
                        message=f"`from {node.module} import *` pollutes the "
                        "namespace and hides where names come from.",
                        line=node.lineno,
                    )
                )
                continue
            self._imported_names[alias.asname or alias.name] = node.lineno
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self._used_names.add(node.id)
        self.generic_visit(node)

    def finalize(self) -> None:
        for name, lineno in self._imported_names.items():
            if name not in self._used_names:
                self.findings.append(
                    Finding(
                        rule_id="unused-import",
                        category=Category.STYLE,
                        severity=Severity.INFO,
                        message=f"`{name}` is imported but never used.",
                        line=lineno,
                    )
                )

        for lineno, line in enumerate(self.lines, start=1):
            if _SECRET_PATTERN.search(line):
                self.findings.append(
                    Finding(
                        rule_id="hardcoded-secret",
                        category=Category.SECURITY,
                        severity=Severity.CRITICAL,
                        message="Possible hardcoded credential or secret. Move "
                        "it to an environment variable or secret manager.",
                        line=lineno,
                    )
                )
            if len(line) > 120:
                self.findings.append(
                    Finding(
                        rule_id="line-too-long",
                        category=Category.STYLE,
                        severity=Severity.INFO,
                        message=f"Line is {len(line)} characters long (limit 120).",
                        line=lineno,
                    )
                )


def analyze_python(source: str) -> list[Finding]:
    """Run all Python static-analysis checks and return the findings.

    Returns a syntax-error finding instead of raising if the source doesn't parse.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [
            Finding(
                rule_id="syntax-error",
                category=Category.BUG,
                severity=Severity.CRITICAL,
                message=f"Code does not parse: {exc.msg}",
                line=exc.lineno,
                column=exc.offset,
            )
        ]

    analyzer = _Analyzer(source)
    analyzer.visit(tree)
    analyzer.finalize()
    return analyzer.findings
