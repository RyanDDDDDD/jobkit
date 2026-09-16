"""Build the plain-text Report block `jobkit render` prints after a batch.

Reads only what `apply` has already written by the time render runs: the
.data.json files just rendered, and {dir}/analysis.md -- derived the same way
render.py derives .rendered.html's directory (apply keeps data at
{dir}/tmp/<name>.data.json, so data_path.parent.parent is {dir}).

No new inputs, no new CLI flags -- everything here is advisory text built
from files the render step already touched.
"""
import json
from pathlib import Path

from jobkit.render import RenderJob, RenderResult

_SELECTED_PROJECTS_TITLES = {"Selected Projects", "精选项目"}


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _has_selected_projects(resume: dict) -> bool:
    return any(
        sec.get("title") in _SELECTED_PROJECTS_TITLES
        for sec in resume.get("sections", [])
    )


def _experience_order(resume: dict) -> list[str]:
    """The company/title sequence of the first `entries` section that has at
    least one dated item -- a Selected Projects section's items never carry
    `dates` (the same discriminator the deleted verify.py used)."""
    for sec in resume.get("sections", []):
        if sec.get("type") != "entries":
            continue
        dated = [it for it in sec.get("items", []) if "dates" in it]
        if dated:
            return [it.get("secondary") or it.get("primary") or "" for it in dated]
    return []


def _analysis_gaps(analysis_path: Path) -> list[str]:
    """Criterion text for every row under '## Criteria → Evidence' whose
    Status cell is exactly 'gap'. A light line scan, not a markdown parser --
    a missing file or an unexpected table shape just yields []."""
    if not analysis_path.is_file():
        return []
    gaps = []
    in_table = False
    for line in analysis_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            in_table = stripped == "## Criteria → Evidence"
            continue
        if not in_table or not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) < 3 or set(cells[0]) <= {"-", ":", ""}:
            continue  # header or separator row
        if cells[-1].lower() == "gap":
            gaps.append(cells[0])
    return gaps


def build_report(jobs: list[RenderJob], results: list[RenderResult]) -> str:
    """jobs/results: the same lists `_cmd_render` already has after
    render_batch, same order, same length. Returns '' when there's nothing to
    report (e.g. an empty batch)."""
    lines: list[str] = []
    resume_data: dict | None = None
    dir_path: Path | None = None

    for job, result in zip(jobs, results):
        data_path = Path(job.data_path).resolve()
        if dir_path is None:
            dir_path = data_path.parent.parent
        name = Path(result.pdf).name
        if not result.ok:
            lines.append(f"  {name}: FAILED — see Render failed message above")
            continue
        data = _load_json(data_path) or {}
        suffix = "" if result.pages == 1 else "s"
        detail = f"lang={data.get('lang', 'en')}"
        if "density" in data:
            detail += f", density={data['density']}"
        lines.append(f"  {name}: OK, {result.pages} page{suffix} ({detail})")
        if "sections" in data:
            resume_data = data

    if resume_data is not None:
        included = "yes" if _has_selected_projects(resume_data) else "no"
        lines.append(f"  Selected Projects included: {included}")
        order = _experience_order(resume_data)
        if order:
            lines.append("  Experience order: " + " -> ".join(order))

    if dir_path is not None:
        gaps = _analysis_gaps(dir_path / "analysis.md")
        if gaps:
            lines.append("  analysis.md gaps not covered: " + "; ".join(gaps))

    if not lines:
        return ""
    return "Report:\n" + "\n".join(lines)
