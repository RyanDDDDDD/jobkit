"""Render an HTML template + JSON data file to a PDF via a headless Chromium
(Playwright's own managed browser).

CLI usage — one or many jobs (the three path flags are repeatable and zipped
positionally):
  uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/render_pdf.py \
      --template-path t1.html --data-path d1.json --out-path o1.pdf \
      [--template-path t2.html --data-path d2.json --out-path o2.pdf ...] \
      [--keep-html]

One browser launch renders every job. Exit 0 iff every job succeeded; 1 if any
failed; 2 on a flag-count mismatch.

Note: with --keep-html the .rendered.html is written next to that job's
--data-path (not --out-path), so it follows the data file into a tmp/ subdirectory.
"""
import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF, used only to count pages after rendering
from playwright.sync_api import sync_playwright

from lib.config import get_job_app_config


@dataclass
class RenderJob:
    template_path: str
    data_path: str
    out_path: str


@dataclass
class RenderResult:
    pdf: str
    pages: int
    ok: bool
    log: str
    html: str | None


def _prepare(job: RenderJob) -> tuple[str, Path, Path]:
    """Resolve paths and splice the data into the template. Returns
    (html, rendered_html_path, out_path). Raises on a missing template/data file."""
    template_path = Path(job.template_path).resolve()
    data_path = Path(job.data_path).resolve()
    out_path = Path(job.out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

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
    return html, rendered_html_path, out_path


def _render_one(browser, job: RenderJob, keep_html: bool) -> RenderResult:
    try:
        html, rendered_html_path, out_path = _prepare(job)
    except Exception as exc:
        return RenderResult(
            pdf=str(Path(job.out_path).resolve()), pages=0, ok=False,
            log=str(exc), html=None,
        )

    ok = False
    pages = 0
    log = ""
    try:
        rendered_html_path.write_text(html, encoding="utf-8")
        page = browser.new_page()
        try:
            # timeout bounds page load/JS execution -- the step that can hang.
            page.goto(rendered_html_path.as_uri(), timeout=60000)
            page.pdf(
                path=str(out_path),
                print_background=True,
                prefer_css_page_size=True,
            )
        finally:
            page.close()

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


def render_batch(jobs: list[RenderJob], keep_html: bool = False) -> list[RenderResult]:
    """Render every job in a single Chromium session. One result per job, in
    order. A job that fails does not stop the rest; a browser-launch failure
    fails every not-yet-attempted job."""
    cfg = get_job_app_config()
    launch_kwargs = {"headless": True}
    if cfg["browser_path"]:
        launch_kwargs["executable_path"] = cfg["browser_path"]

    results: list[RenderResult] = []
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(**launch_kwargs)
            try:
                for job in jobs:
                    results.append(_render_one(browser, job, keep_html))
            finally:
                browser.close()
    except Exception as exc:
        for job in jobs[len(results):]:
            results.append(RenderResult(
                pdf=str(Path(job.out_path).resolve()), pages=0, ok=False,
                log=f"browser launch failed: {exc}", html=None,
            ))
    return results


def render_pdf(
    template_path: str,
    data_path: str,
    out_path: str,
    keep_html: bool = False,
) -> RenderResult:
    """Render a single template+data pair to a PDF (one-job wrapper over render_batch)."""
    return render_batch(
        [RenderJob(template_path, data_path, out_path)], keep_html=keep_html
    )[0]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--template-path", action="append", required=True)
    parser.add_argument("--data-path", action="append", required=True)
    parser.add_argument("--out-path", action="append", required=True)
    parser.add_argument("--keep-html", action="store_true")
    args = parser.parse_args()

    if not (len(args.template_path) == len(args.data_path) == len(args.out_path)):
        print(
            "render_pdf: --template-path, --data-path and --out-path must each be "
            "given the same number of times",
            file=sys.stderr,
        )
        sys.exit(2)

    jobs = [
        RenderJob(t, d, o)
        for t, d, o in zip(args.template_path, args.data_path, args.out_path)
    ]
    results = render_batch(jobs, keep_html=args.keep_html)

    any_failed = False
    for r in results:
        if r.ok:
            suffix = "" if r.pages == 1 else "s"
            print(f"OK: {r.pdf} ({r.pages} page{suffix})")
        else:
            any_failed = True
            print(f"Render failed [{r.pdf}]:\n{r.log}", file=sys.stderr)
    sys.exit(1 if any_failed else 0)


if __name__ == "__main__":
    main()
