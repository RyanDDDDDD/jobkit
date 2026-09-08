"""Scaffold a fresh working directory for the job-application (jobkit) plugin.

Creates jobapp.config.yml, CLAUDE.md, the private/ subtree (resume_sections/
templates + a seeded interview_playbook.md + questions_to_ask.md), and an empty
applications/ directory. Strictly non-destructive: a file that already exists is
never read, modified, or deleted.

CLI usage: jobkit init [target] [--json]
prints a created/skipped summary (default) or a JSON object with --json.
"""
import argparse
import json
import shutil
import sys
from pathlib import Path

from jobkit._assets import resource_text, templates_dir

# Empty directories to ensure exist (mkdir -p); git does not track them.
SCAFFOLD_DIRS = (
    "applications",
    "private/resume_sections/companies",
    "private/resume_sections/projects",
)


def init_workspace(target: str) -> dict:
    """Scaffold `target`. Return {"created": [...], "skipped": [...], "warnings": [...]}
    of paths relative to `target` (POSIX form, sorted). Never modifies an existing file."""
    root = Path(target).resolve()
    template_root = templates_dir() / "workspace"
    if not template_root.is_dir():
        raise FileNotFoundError(f"template bundle missing: {template_root}")

    config_existed = (root / "jobapp.config.yml").exists()

    created: list[str] = []
    skipped: list[str] = []
    warnings: list[str] = []

    def place(dest: Path, src: Path) -> None:
        rel = dest.relative_to(root).as_posix()
        if dest.exists():
            skipped.append(rel)
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        created.append(rel)

    # 1. Copy every template file, preserving the relative layout.
    for src in sorted(p for p in template_root.rglob("*") if p.is_file()):
        place(root / src.relative_to(template_root), src)

    # 2. Seed the interview playbook from the plugin's framework reference.
    playbook = root / "private" / "interview_playbook.md"
    if playbook.exists():
        skipped.append(playbook.relative_to(root).as_posix())
    else:
        playbook.parent.mkdir(parents=True, exist_ok=True)
        playbook.write_text(
            resource_text("reference/interview-frameworks.md"), encoding="utf-8"
        )
        created.append(playbook.relative_to(root).as_posix())

    # 3. Ensure the empty scaffold directories exist.
    for d in SCAFFOLD_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)

    if not config_existed:
        for legacy in ("resume_sections", "interview_playbook.md"):
            if (root / legacy).exists():
                warnings.append(
                    f"'{legacy}' already exists at the workspace root, but the "
                    f"jobapp.config.yml just written points at 'private/{legacy}'. "
                    f"Move the existing content under private/, or edit jobapp.config.yml."
                )

    created.sort()
    skipped.sort()
    warnings.sort()
    return {"created": created, "skipped": skipped, "warnings": warnings}


def _format_summary(result: dict, target: str) -> str:
    lines = [f"Workspace: {Path(target).resolve()}", ""]
    for path in result["created"]:
        lines.append(f"  {'created':<18}{path}")
    for path in result["skipped"]:
        lines.append(f"  {'exists (skipped)':<18}{path}")
    if result["warnings"]:
        lines.append("")
        for warning in result["warnings"]:
            lines.append(f"WARNING: {warning}")
    lines.append("")
    if result["created"]:
        lines.append(
            "Next: fill in private/resume_sections/profile.yml and "
            "private/resume_sections/factual-bounds.md, then run "
            "/job-application:setup <folder of your old CVs> (or hand-fill the "
            "section files), then /job-application:apply."
        )
    else:
        lines.append("Workspace already initialised - nothing to do.")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", default=".")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args()
    try:
        result = init_workspace(args.target)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result) if args.json else _format_summary(result, args.target))


if __name__ == "__main__":
    main()
