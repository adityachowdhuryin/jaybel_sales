#!/usr/bin/env python3
"""Build PROJECT_ARCHITECTURE_GUIDE.pdf from markdown + rendered Mermaid diagrams."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
MD_PATH = DOCS / "PROJECT_ARCHITECTURE_GUIDE.md"
HTML_PATH = DOCS / "PROJECT_ARCHITECTURE_GUIDE_PRINT.html"
PDF_PATH = DOCS / "PROJECT_ARCHITECTURE_GUIDE.pdf"
PDF_SCRIPT = ROOT / "scripts" / "html_to_pdf.mjs"


def prepare_markdown(text: str) -> str:
    """Strip editor-only notes; keep mermaid blocks; drop duplicate SVG image lines."""
    lines = text.splitlines()
    out: list[str] = []
    skip_blockquote = False
    for line in lines:
        if line.strip() == "> **How to view diagrams**":
            skip_blockquote = True
            continue
        if skip_blockquote:
            if line.startswith("> ") or (line.strip() == "" and out and out[-1].startswith(">")):
                continue
            if not line.startswith(">"):
                skip_blockquote = False
        if skip_blockquote:
            continue
        if re.match(r"^!\[.*\]\(diagrams/.*\.svg\)\s*$", line):
            continue
        out.append(line)
    return "\n".join(out)


def mermaid_to_div_blocks(text: str) -> str:
    """Replace fenced mermaid with div.mermaid for Mermaid.js."""

    def repl(m: re.Match[str]) -> str:
        body = m.group(1).strip()
        return f'<div class="mermaid">\n{body}\n</div>'

    return re.sub(r"```mermaid\n(.*?)```", repl, text, flags=re.DOTALL)


def md_to_html_body(md: str) -> str:
    import markdown

    md = mermaid_to_div_blocks(md)
    # Prevent markdown from wrapping div.mermaid in <p>
    md = md.replace('<div class="mermaid">', '\n\n<div class="mermaid">')
    html = markdown.markdown(
        md,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"],
    )
    return html


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Jaybel Sales Analytics — Architecture Guide</title>
  <style>
    @page { size: A4; margin: 18mm 14mm; }
    body {
      font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
      font-size: 11pt;
      line-height: 1.45;
      color: #1e293b;
      max-width: 100%;
      margin: 0;
      padding: 0 4mm;
    }
    h1 { font-size: 22pt; color: #0f172a; border-bottom: 3px solid #0ea5e9; padding-bottom: 8px; page-break-after: avoid; }
    h2 { font-size: 15pt; color: #0f172a; margin-top: 1.4em; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; page-break-after: avoid; }
    h3 { font-size: 12pt; color: #334155; page-break-after: avoid; }
    p, li { orphans: 3; widows: 3; }
    table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 10pt; page-break-inside: avoid; }
    th, td { border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; vertical-align: top; }
    th { background: #f1f5f9; font-weight: 600; }
    tr:nth-child(even) td { background: #f8fafc; }
    code { font-family: ui-monospace, monospace; font-size: 9pt; background: #f1f5f9; padding: 1px 4px; border-radius: 3px; }
    pre { background: #f1f5f9; padding: 10px; border-radius: 6px; font-size: 9pt; overflow-x: auto; page-break-inside: avoid; }
    pre code { background: none; padding: 0; }
    blockquote { border-left: 4px solid #0ea5e9; margin: 12px 0; padding: 8px 16px; background: #f0f9ff; color: #334155; }
    .mermaid {
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 16px;
      margin: 16px 0;
      text-align: center;
      page-break-inside: avoid;
    }
    .mermaid svg { max-width: 100% !important; height: auto !important; }
    hr { border: none; border-top: 1px solid #e2e8f0; margin: 24px 0; }
    .cover {
      text-align: center;
      padding: 48px 24px 32px;
      page-break-after: always;
    }
    .cover h1 { border: none; font-size: 26pt; }
    .cover p { color: #64748b; font-size: 12pt; }
    .toc { page-break-after: always; }
    .toc ol { line-height: 1.8; }
    a { color: #0369a1; text-decoration: none; }
    .footer-note { font-size: 9pt; color: #64748b; margin-top: 24px; }
  </style>
</head>
<body>
  <div class="cover">
    <h1>Jaybel Sales Analytics</h1>
    <p><strong>Complete Architecture Guide</strong></p>
    <p>Natural Language → SQL Agent · Local App + Google Cloud</p>
    <p style="margin-top:32px;font-size:10pt;">jaybel-dev · Vertex AI Agent Engine · BigQuery</p>
  </div>
  <div class="toc">
    <h2>Contents</h2>
    <ol>
      <li>What is this project?</li>
      <li>The big picture — two worlds</li>
      <li>Main components</li>
      <li>End-to-end journey</li>
      <li>Pipeline L1–L5</li>
      <li>Where data lives</li>
      <li>Schema registry</li>
      <li>Agent Engine</li>
      <li>Question discovery UI</li>
      <li>UI building blocks</li>
      <li>Streaming events</li>
      <li>Special cases (v1.2 / v1.3)</li>
      <li>Repository map</li>
      <li>Running locally</li>
      <li>Security model</li>
      <li>Out of scope for v1</li>
      <li>Deeper reading</li>
      <li>One-page mental model</li>
    </ol>
  </div>
  {body}
  <p class="footer-note">Generated from docs/PROJECT_ARCHITECTURE_GUIDE.md — v1 local app, v1.2 targets/patterns, v1.3 charts/markdown, Phase D QA.</p>
  <script type="module">
    import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";
    mermaid.initialize({
      startOnLoad: false,
      theme: "neutral",
      securityLevel: "loose",
      flowchart: { useMaxWidth: true, htmlLabels: true },
      sequence: { useMaxWidth: true },
    });
    await mermaid.run();
    document.documentElement.setAttribute("data-mermaid-ready", "true");
  </script>
</body>
</html>
"""


def build_html() -> None:
    raw = MD_PATH.read_text(encoding="utf-8")
    md = prepare_markdown(raw)
    body = md_to_html_body(md)
    # Remove duplicate h1 from md (we have cover)
    body = re.sub(r"<h1>.*?</h1>\s*", "", body, count=1, flags=re.DOTALL)
    html = HTML_TEMPLATE.replace("{body}", body)
    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"Wrote {HTML_PATH}")


def build_pdf() -> None:
    if not PDF_SCRIPT.exists():
        raise FileNotFoundError(PDF_SCRIPT)
    subprocess.run(
        ["node", str(PDF_SCRIPT), str(HTML_PATH), str(PDF_PATH)],
        check=True,
        cwd=str(ROOT),
    )
    print(f"Wrote {PDF_PATH}")


def main() -> int:
    build_html()
    try:
        build_pdf()
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"PDF step failed: {e}", file=sys.stderr)
        print(f"Open {HTML_PATH} in Chrome → Print → Save as PDF", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
