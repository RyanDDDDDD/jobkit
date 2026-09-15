"""Render an HTML template + JSON data file to a PDF via a headless Chromium
(Playwright's own managed browser).

CLI usage — one or many jobs (--kind / --data / --out are repeatable, zipped
positionally):
  jobkit render --kind resume --data d1.json --out o1.pdf \
      [--kind cover_letter --data d2.json --out o2.pdf ...] [--keep-html]

One browser launch renders every job. Exit 0 iff every job succeeded; 1 if any
failed; 2 on a flag-count mismatch.

Note: with --keep-html the .rendered.html is written next to that job's
--data (not --out), so it follows the data file into a tmp/ subdirectory.
"""
from dataclasses import dataclass
from pathlib import Path

import pymupdf  # used only to count pages after rendering
from playwright.sync_api import sync_playwright

from jobkit.config import get_job_app_config


def _resolve_font_dir(template_path: Path) -> Path:
    """Locate the fonts/ directory for a template HTML file.

    Precedence: sibling ``fonts/`` (workspace override or flat layout), then
    parent ``fonts/`` (bundled ``templates/<theme>/*.html`` → ``templates/fonts``).
    """
    sibling = template_path.parent / "fonts"
    if sibling.is_dir():
        return sibling
    parent_fonts = template_path.parent.parent / "fonts"
    if parent_fonts.is_dir():
        return parent_fonts
    return sibling


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
    # bundled-font url("fonts/...") strings to absolute file:/// paths so the
    # woff2 faces load instead of falling back. Themes live under
    # templates/<theme>/; shared fonts live under templates/fonts/. A workspace
    # override may keep fonts next to the HTML instead.
    font_dir = _resolve_font_dir(template_path)
    font_dir_url = font_dir.as_uri() + "/"
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
            doc = pymupdf.open(out_path)
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
