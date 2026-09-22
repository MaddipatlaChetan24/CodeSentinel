"""CodeSentinel command-line interface.

    codesentinel review --file path/to/code.py
    codesentinel review --code "def add(a,b): return a+b"
    codesentinel review --file app.js --language javascript --format json
    codesentinel serve --port 8000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codesentinel.providers import first_available, get_provider
from codesentinel.review import export, review_source
from codesentinel.rules import RuleConfig


def _cmd_review(args: argparse.Namespace) -> int:
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        source = path.read_text()
        target = str(path)
        language = args.language or _guess_language(path)
    else:
        source = args.code
        target = "<inline>"
        language = args.language or "python"

    provider = None
    if not args.no_llm:
        provider = get_provider(args.provider) if args.provider else first_available()

    rule_config = RuleConfig.load(args.config)

    result = review_source(
        source,
        language=language,
        target=target,
        provider=provider,
        rule_config=rule_config,
    )

    output = export(result, args.format)
    if args.output:
        Path(args.output).write_text(output)
        print(f"Wrote {args.format} report to {args.output}")
    else:
        print(output)

    if args.fail_on and result.score < args.fail_on:
        print(f"\nScore {result.score} is below --fail-on threshold {args.fail_on}", file=sys.stderr)
        return 2
    return 0


def _guess_language(path: Path) -> str:
    return {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".go": "go",
        ".java": "java",
        ".rb": "ruby",
    }.get(path.suffix, "text")


def _cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("codesentinel.web.app:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codesentinel", description="CodeSentinel code review agent")
    sub = parser.add_subparsers(dest="command", required=True)

    review_p = sub.add_parser("review", help="Review a file or code snippet")
    group = review_p.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Path to file to review")
    group.add_argument("--code", help="Inline code snippet to review")
    review_p.add_argument("--language", help="Programming language (auto-detected for --file)")
    review_p.add_argument(
        "--provider",
        choices=["openai", "anthropic", "ollama"],
        help="LLM provider to use for the narrative insight pass (auto-selected if omitted)",
    )
    review_p.add_argument("--no-llm", action="store_true", help="Skip the LLM pass, static analysis only")
    review_p.add_argument("--format", choices=["markdown", "json", "html"], default="markdown")
    review_p.add_argument("--output", help="Write the report to a file instead of stdout")
    review_p.add_argument("--config", help="Path to .codesentinel.yml rule config (default: ./.codesentinel.yml)")
    review_p.add_argument(
        "--fail-on",
        type=int,
        default=0,
        metavar="SCORE",
        help="Exit with code 2 if the review score is below this threshold (for CI)",
    )
    review_p.set_defaults(func=_cmd_review)

    serve_p = sub.add_parser("serve", help="Run the web dashboard")
    serve_p.add_argument("--host", default="127.0.0.1")
    serve_p.add_argument("--port", type=int, default=8000)
    serve_p.add_argument("--reload", action="store_true")
    serve_p.set_defaults(func=_cmd_serve)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
