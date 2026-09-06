"""Render an HTML template + JSON data file to a PDF via a headless Chromium
(Playwright's own managed browser), preserving render_pdf.py's CLI contract.

CLI usage:
  uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/render_pdf.py \
      --template-path t.html --data-path d.json --out-path o.pdf \
      [--keep-html]

Note: with --keep-html the .rendered.html is written next to --data-path (not
--out-path), so it follows the data file into a tmp/ subdirectory.
"""
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF, used only to count pages after rendering
from playwright.sync_api import sync_playwright

from lib.config import get_job_app_config


@dataclass
class RenderResult:
    pdf: str
    pages: int
    ok: bool
    log: str
    html: str | None


def render_pdf(
    template_path: str,
    data_path: str,
    out_path: str,
    keep_html: bool = False,
) -> RenderResult:
    template_path = Path(template_path).resolve()
    data_path = Path(data_path).resolve()
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    cfg = get_job_app_config()

    tpl = template_path.read_text(encoding="utf-8")
    json_text = data_path.read_text(encoding="utf-8")
    # The JSON is spliced verbatim into <script type="application/json">. A data
    # string containing "</script>" would close that element early and break
    # JSON.parse; '<\/' is a legal JSON escape, invisible after parsing, and can
    # never terminate the element.
    json_text = json_text.replace("</", "<\\/")
    html = tpl.replace("{{DATA_JSON}}", json_text)

    # Chromium resolves relative url() against the page's URL. Rewrite the
    # bundled-font url("fonts/...") strings to absolute file:/// paths at the
    # template's own fonts/ dir so the woff2 faces load instead of falling back.
    font_dir_url = (template_path.parent / "fonts").as_uri() + "/"
    html = html.replace('url("fonts/', f'url("{font_dir_url}')

    # The .rendered.html is the data spliced into the template -- a sibling of the
    # data file, not the output PDF. `apply` keeps the data in {dir}/tmp/ while
    # the PDF lands flat in {dir}/, so derive the dir from data_path.
    rendered_html_path = data_path.parent / (out_path.stem + ".rendered.html")

    ok = False
    pages = 0
    log = ""
    try:
        rendered_html_path.write_text(html, encoding="utf-8")

        with sync_playwright() as p:
            launch_kwargs = {"headless": True}
            # Playwright always launches its own isolated browser instance/profile
            # (unlike the old --user-data-dir workaround, it never hands off to a
            # browser the user already has open), so no throwaway profile dir is
            # needed here.
            if cfg["browser_path"]:
                launch_kwargs["executable_path"] = cfg["browser_path"]
            browser = p.chromium.launch(**launch_kwargs)
            try:
                page = browser.new_page()
                # timeout bounds page load/JS execution — the step that can hang.
                page.goto(rendered_html_path.as_uri(), timeout=60000)
                page.pdf(
                    path=str(out_path),
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()

        ok = out_path.is_file() and out_path.stat().st_size > 0
        if ok:
            doc = fitz.open(out_path)
            try:
                pages = len(doc)
            finally:
                doc.close()
    except Exception as exc:
        log = str(exc)
        ok = False
    finally:
        if not keep_html and rendered_html_path.is_file():
            rendered_html_path.unlink()

    return RenderResult(
        pdf=str(out_path),
        pages=pages,
        ok=ok,
        log=log,
        html=str(rendered_html_path) if keep_html else None,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-path", required=True)
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--out-path", required=True)
    parser.add_argument("--keep-html", action="store_true")
    args = parser.parse_args()

    result = render_pdf(
        args.template_path, args.data_path, args.out_path, args.keep_html
    )
    if result.ok:
        suffix = "" if result.pages == 1 else "s"
        print(f"OK: {result.pdf} ({result.pages} page{suffix})")
    else:
        print(f"Render failed:\n{result.log}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
