"""Locate bundled package data (templates, reference docs) without any
path computed from __file__. Uses importlib.resources so it works from a
wheel, an editable install, or a zipimport."""
from __future__ import annotations

import importlib.resources as ir
from contextlib import ExitStack
from pathlib import Path

RESUME_TEMPLATES = ("dossier", "classic", "modern-sans", "signal", "slate")
DEFAULT_RESUME_TEMPLATE = "dossier"
LANGS = ("en", "zh")
DEFAULT_LANG = "en"

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


def template_path(kind: str, theme: str | None = None) -> Path:
    """Filesystem path to a bundled résumé / cover-letter HTML template.

    Themes live under ``templates/<theme>/{resume,cover_letter}.html``.
    Shared fonts live under ``templates/fonts/``.
    """
    if kind not in _TEMPLATE_FILE:
        raise KeyError(f"unknown template kind: {kind!r}")
    theme = theme or DEFAULT_RESUME_TEMPLATE
    if theme not in RESUME_TEMPLATES:
        raise ValueError(
            f"unknown resume_template {theme!r}; choose one of: "
            f"{', '.join(RESUME_TEMPLATES)}"
        )
    return _as_path("templates", theme, _TEMPLATE_FILE[kind])


def resolve_template_path(
    kind: str,
    *,
    theme: str | None = None,
    explicit: str | None = None,
    root: str | Path | None = None,
) -> Path:
    """Resolve a template path with override precedence:

    1. ``explicit`` (``--template`` CLI flag)
    2. workspace ``<root>/templates/<resume|cover_letter>.html`` if present
    3. bundled ``templates/<theme>/…``
    """
    if explicit:
        return Path(explicit)
    if root is not None:
        override = Path(root) / "templates" / _TEMPLATE_FILE[kind]
        if override.is_file():
            return override
    return template_path(kind, theme)
