"""Guards the portability invariant: no host-specific path variable or `uv`
invocation may live in a skill or agent body, and skill/agent frontmatter
stays within the cross-tool-safe field subset."""
import re
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]
SKILL_FILES = sorted((PLUGIN / "skills").rglob("SKILL.md"))
AGENT_FILES = sorted((PLUGIN / "agents").glob("*.md"))
ALL = SKILL_FILES + AGENT_FILES

FORBIDDEN = re.compile(r"CLAUDE_PLUGIN_ROOT|CLAUDE_PLUGIN_DATA|PLUGIN_ROOT|uv run|uv tool|\buvx\b")

SKILL_FM_ALLOWED = {"name", "description", "disable-model-invocation"}
AGENT_FM_ALLOWED = {"name", "description", "model", "tools", "readonly"}


def _frontmatter_keys(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return set()
    fm = text.split("---", 2)[1]
    return {line.split(":", 1)[0].strip()
            for line in fm.splitlines() if line.strip() and ":" in line
            and not line.startswith((" ", "\t", "-"))}


def test_files_found():
    assert len(SKILL_FILES) == 3
    assert len(AGENT_FILES) == 2


@pytest.mark.parametrize("path", ALL, ids=lambda p: p.relative_to(PLUGIN).as_posix())
def test_no_host_specific_paths(path):
    hits = [f"{i}: {ln}" for i, ln in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
            if FORBIDDEN.search(ln)]
    assert not hits, "\n".join(hits)


@pytest.mark.parametrize("path", SKILL_FILES, ids=lambda p: p.parent.name)
def test_skill_frontmatter_subset(path):
    assert _frontmatter_keys(path) <= SKILL_FM_ALLOWED, _frontmatter_keys(path)


@pytest.mark.parametrize("path", AGENT_FILES, ids=lambda p: p.stem)
def test_agent_frontmatter_subset(path):
    assert _frontmatter_keys(path) <= AGENT_FM_ALLOWED, _frontmatter_keys(path)
