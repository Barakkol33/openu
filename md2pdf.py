"""Render a summary README-style markdown file to a dense, print-ready PDF.

Math ($...$, $$...$$) is rendered with KaTeX and images (e.g. SVG diagrams) are
resolved relative to the markdown file. Printing is done by headless Chrome/Edge.

Usage:
    python md2pdf.py computational-models/summary.md [--out X.pdf] [--columns 2] [--font-size 9.3]
"""

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin

KATEX = "https://cdn.jsdelivr.net/npm/katex@0.16.11/dist"

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "google-chrome",
    "chromium",
]

TEMPLATE = """<!doctype html>
<html dir="{dir}"><head><meta charset="utf-8">
<base href="{base}">
<link rel="stylesheet" href="{katex}/katex.min.css">
<script src="{katex}/katex.min.js"></script>
<style>
@page {{ size: A4; margin: 7mm 7mm 8mm 7mm; }}
html {{ font-family: "Segoe UI", Arial, Helvetica, Arial, sans-serif; font-size: {font_size}pt; line-height: 1.28; color: #111; }}
body {{ margin: 0; }}
.cols {{ column-count: {columns}; column-gap: 5mm; column-rule: 0.4pt solid #ccc; }}
h1 {{ font-size: 1.55em; margin: 0 0 0.2em; column-span: all; }}
h1 + p {{ column-span: all; margin-top: 0; color: #444; }}
h2 {{ font-size: 1.25em; margin: 0.35em 0 0.2em; padding: 0.1em 0.35em; background: #1e3a8a; color: #fff; border-radius: 3px; break-after: avoid; }}
h3 {{ font-size: 1.06em; margin: 0.45em 0 0.12em; color: #1e3a8a; border-bottom: 0.6pt solid #93c5fd; break-after: avoid; }}
p {{ margin: 0.2em 0; }}
ul, ol {{ margin: 0.1em 0 0.2em; padding-inline-start: 1.15em; }}
li {{ margin: 0.04em 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 0.2em 0 0.3em; break-inside: avoid; }}
th, td {{ border: 0.4pt solid #bbb; padding: 0.05em 0.25em; vertical-align: top; text-align: start; }}
th {{ background: #eff6ff; }}
code {{ direction: ltr; unicode-bidi: isolate; font-family: Consolas, monospace; font-size: 0.95em; background: #f3f4f6; padding: 0 0.15em; border-radius: 2px; }}
pre {{ background: #f3f4f6; padding: 0.25em 0.4em; margin: 0.2em 0; white-space: pre-wrap; break-inside: avoid; }}
pre code {{ background: none; padding: 0; }}
blockquote {{ margin: 0.25em 0; padding: 0.15em 0.45em; border-inline-start: 2.5pt solid #f59e0b; background: #fffbeb; break-inside: avoid; }}
blockquote p {{ margin: 0.1em 0; }}
img {{ width: 100%; display: block; margin: 0.2em 0; break-inside: avoid; }}
hr {{ display: none; }}
.katex {{ font-size: 1.02em; direction: ltr; unicode-bidi: isolate; }}
.math.block {{ margin: 0.2em 0; text-align: center; }}
</style></head>
<body><div class="cols">{body}</div>
<script>
document.querySelectorAll(".math").forEach(el => {{
  katex.render(el.textContent, el, {{ displayMode: el.classList.contains("block"), throwOnError: false }});
}});
</script>
</body></html>
"""


def find_browser():
    for b in BROWSERS:
        if Path(b).exists() or shutil.which(b):
            return b
    raise SystemExit("Chrome / Edge not found")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("markdown")
    ap.add_argument("--out")
    ap.add_argument("--columns", type=int, default=2)
    ap.add_argument("--font-size", type=float, default=9.3)
    args = ap.parse_args()

    src = Path(args.markdown).resolve()
    out = Path(args.out).resolve() if args.out else src.with_suffix(".pdf")

    text = src.read_text(encoding="utf-8")
    md = MarkdownIt("commonmark").enable("table").use(dollarmath_plugin)
    html = TEMPLATE.format(
        # Hebrew summaries are laid out right-to-left; math and code stay LTR.
        dir="rtl" if any("֐" <= c <= "׿" for c in text) else "ltr",
        base=src.parent.as_uri() + "/",
        katex=KATEX,
        font_size=args.font_size,
        columns=args.columns,
        body=md.render(text),
    )

    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [
                find_browser(),
                "--headless=new",
                "--disable-gpu",
                "--no-pdf-header-footer",
                "--allow-file-access-from-files",
                "--virtual-time-budget=15000",
                f"--print-to-pdf={out}",
                page.as_uri(),
            ],
            check=True,
            capture_output=True,
        )

    try:
        import pymupdf

        print(f"{out} ({pymupdf.open(out).page_count} pages)")
    except ImportError:
        print(out)


if __name__ == "__main__":
    main()
