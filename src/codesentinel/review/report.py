"""Export a ReviewResult as JSON, Markdown, or a standalone HTML report."""

from __future__ import annotations

import json
from html import escape

from .models import ReviewResult


def to_json(result: ReviewResult) -> str:
    return json.dumps(result.to_dict(), indent=2)


def to_markdown(result: ReviewResult) -> str:
    lines = [
        f"# Code Review: `{result.target}`",
        "",
        f"**Score:** {result.score}/100 — {result.verdict}",
        f"**Language:** {result.language}  ",
        f"**Duration:** {result.duration_seconds:.2f}s",
        "",
    ]

    if result.findings:
        lines.append("## Findings\n")
        for f in result.findings:
            loc = f" (line {f.line})" if f.line else ""
            lines.append(
                f"- **[{f.severity.value.upper()}] [{f.category.value}] {f.rule_id}**{loc}: {f.message}"
            )
        lines.append("")
    else:
        lines.append("No static findings.\n")

    if result.llm_summary:
        lines.append(f"## LLM Insight ({result.llm_provider or 'n/a'})\n")
        lines.append(result.llm_summary)
        lines.append("")

    return "\n".join(lines)


def to_html(result: ReviewResult) -> str:
    rows = "".join(
        f"""
        <tr class="sev-{f.severity.value}">
          <td>{escape(f.severity.value)}</td>
          <td>{escape(f.category.value)}</td>
          <td>{escape(f.rule_id)}</td>
          <td>{f.line or '-'}</td>
          <td>{escape(f.message)}</td>
        </tr>"""
        for f in result.findings
    )

    llm_block = ""
    if result.llm_summary:
        llm_block = f"""
        <h2>LLM Insight ({escape(result.llm_provider or 'n/a')})</h2>
        <pre class="llm">{escape(result.llm_summary)}</pre>
        """

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Review: {escape(result.target)}</title>
<style>
  body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 2rem auto; color: #1a1a1a; }}
  h1 {{ margin-bottom: 0; }}
  .score {{ font-size: 1.5rem; margin-top: .25rem; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
  th, td {{ text-align: left; padding: .5rem; border-bottom: 1px solid #e5e5e5; }}
  tr.sev-critical {{ background: #fde8e8; }}
  tr.sev-high {{ background: #fdf1e0; }}
  tr.sev-medium {{ background: #fdfbe0; }}
  pre.llm {{ white-space: pre-wrap; background: #f6f6f6; padding: 1rem; border-radius: 8px; }}
</style>
</head>
<body>
  <h1>Code Review: {escape(result.target)}</h1>
  <div class="score">{result.score}/100 — {escape(result.verdict)}</div>
  <p>{escape(result.language)} · {result.duration_seconds:.2f}s · {len(result.findings)} findings</p>
  <table>
    <thead><tr><th>Severity</th><th>Category</th><th>Rule</th><th>Line</th><th>Message</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  {llm_block}
</body>
</html>"""


def export(result: ReviewResult, fmt: str) -> str:
    fmt = fmt.lower()
    if fmt == "json":
        return to_json(result)
    if fmt == "markdown" or fmt == "md":
        return to_markdown(result)
    if fmt == "html":
        return to_html(result)
    raise ValueError(f"Unknown export format: {fmt}")
