"""Locate bundled package data (templates, reference docs) without any
path computed from __file__. Uses importlib.resources so it works from a
wheel, an editable install, or a zipimport."""
from __future__ import annotations

import importlib.resources as ir
from contextlib import ExitStack
from pathlib import Path

_TEMPLATE_FILE = {
    "resume": "resume.html",
    "cover_letter": "cover_letter.html",
}

# Keep extracted resources alive for the process lifetime.
_STACK = ExitStack()


def _as_path(*parts: str) -> Path:
    res = ir.files("jobkit").joinpath(*parts)
    return _STACK.enter_context(ir.as_file(res))


def resource_text(relpath: str) -> str:
    """UTF-8 text of a file under the jobkit package, e.g.
    resource_text("reference/workflow-rules.md")."""
    return ir.files("jobkit").joinpath(*relpath.split("/")).read_text(encoding="utf-8")


def templates_dir() -> Path:
    """Filesystem path to the bundled templates/ directory."""
    return _as_path("templates")


def template_path(kind: str) -> Path:
    """Filesystem path to the bundled résumé / cover-letter HTML template."""
    return _as_path("templates", _TEMPLATE_FILE[kind])
