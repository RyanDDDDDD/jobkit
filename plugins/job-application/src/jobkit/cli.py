"""`jobkit` command-line entry point. Each subcommand is a 1:1 shim over a
package function; no behaviour lives here that is not in the old scripts."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

from jobkit import __version__
from jobkit._assets import (
    LANGS,
    RESUME_TEMPLATES,
    resolve_template_path,
)
from jobkit.compress import compress_pdf
from jobkit.config import get_job_app_config
from jobkit.cover_txt import cover_letter_to_text
from jobkit.docs import DOC_NAMES, read_doc
from jobkit.extract_cv import extract_text
from jobkit.init_workspace import init_workspace
from jobkit.render import RenderJob, render_batch
from jobkit.scaffold import scaffold_data


def _cmd_config(a) -> int:
    print(json.dumps(get_job_app_config()))
    return 0


def _cmd_render(a) -> int:
    n = len(a.kind)
    if not (n == len(a.data) == len(a.out)):
        print("jobkit render: --kind, --data and --out must each be given the "
              "same number of times", file=sys.stderr)
        return 2
    cfg = get_job_app_config()
    theme = cfg.get("resume_template")
    templates = a.template or []
    templates += [None] * (n - len(templates))
    jobs = []
    for kind, data, out, tpl in zip(a.kind, a.data, a.out, templates):
        tp = str(resolve_template_path(
            kind, theme=theme, explicit=tpl, root=cfg["root"],
        ))
        jobs.append(RenderJob(tp, data, out))
    results = render_batch(jobs, keep_html=a.keep_html)
    any_failed = False
    for r in results:
        if r.ok:
            suffix = "" if r.pages == 1 else "s"
            print(f"OK: {r.pdf} ({r.pages} page{suffix})")
        else:
            any_failed = True
            print(f"Render failed [{r.pdf}]:\n{r.log}", file=sys.stderr)
    return 1 if any_failed else 0


def _cmd_compress(a) -> int:
    for p in a.pdf:
        print(compress_pdf(p))
    return 0


def _cmd_cover_txt(a) -> int:
    cover_letter_to_text(a.data, a.out)
    print(f"OK: {a.out}" if a.out else "OK: cover_letter.txt")
    return 0


def _cmd_scaffold_data(a) -> int:
    lang = a.lang
    if lang is None:
        lang = get_job_app_config().get("lang", "en")
    try:
        result = scaffold_data(a.dir, a.source_dir, lang, a.density)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Wrote {result['resume']}")
    print(f"Wrote {result['cover_letter']}")
    return 0


def _cmd_extract_cv(a) -> int:
    try:
        print(extract_text(a.path), end="")
    except Exception as exc:
        print(f"jobkit extract-cv: {exc}", file=sys.stderr)
        return 2
    return 0


def _cmd_init(a) -> int:
    try:
        result = init_workspace(a.target, a.lang, a.resume_template)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps(result))
    else:
        from jobkit.init_workspace import _format_summary
        print(_format_summary(result, a.target))
    return 0


def _cmd_doc(a) -> int:
    try:
        print(read_doc(a.name))
    except KeyError:
        print(f"jobkit doc: unknown doc {a.name!r}; choose one of: "
              f"{', '.join(DOC_NAMES)}", file=sys.stderr)
        return 2
    return 0


def _cmd_install_browser(a) -> int:
    return subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"]
    ).returncode


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jobkit")
    p.add_argument("--version", action="version", version=f"jobkit {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("config"); s.add_argument("--json", action="store_true")
    s.set_defaults(fn=_cmd_config)

    s = sub.add_parser("render")
    s.add_argument("--kind", action="append", required=True,
                   choices=["resume", "cover_letter"])
    s.add_argument("--data", action="append", required=True)
    s.add_argument("--out", action="append", required=True)
    s.add_argument("--template", action="append", default=None)
    s.add_argument("--keep-html", action="store_true")
    s.set_defaults(fn=_cmd_render)

    s = sub.add_parser("compress"); s.add_argument("--pdf", action="append", required=True)
    s.set_defaults(fn=_cmd_compress)

    s = sub.add_parser("cover-txt")
    s.add_argument("--data", required=True); s.add_argument("--out", default=None)
    s.set_defaults(fn=_cmd_cover_txt)

    s = sub.add_parser("scaffold-data")
    s.add_argument("--dir", required=True); s.add_argument("--source-dir", required=True)
    s.add_argument("--lang", default=None, choices=list(LANGS),
                   help="default: jobapp.config.yml lang, else en")
    s.add_argument("--density", choices=["compact", "standard"])
    s.set_defaults(fn=_cmd_scaffold_data)

    s = sub.add_parser("extract-cv"); s.add_argument("path")
    s.set_defaults(fn=_cmd_extract_cv)

    s = sub.add_parser("init")
    s.add_argument("target", nargs="?", default=".")
    s.add_argument("--lang", required=True, choices=list(LANGS),
                   help="workspace output language (en|zh)")
    s.add_argument("--template", required=True, choices=list(RESUME_TEMPLATES),
                   dest="resume_template",
                   help="bundled résumé theme (dossier|classic|modern-sans)")
    s.add_argument("--json", action="store_true")
    s.set_defaults(fn=_cmd_init)

    s = sub.add_parser("doc"); s.add_argument("name")
    s.set_defaults(fn=_cmd_doc)

    s = sub.add_parser("install-browser")
    s.set_defaults(fn=_cmd_install_browser)

    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
