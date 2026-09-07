import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from init_workspace import init_workspace  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SKELETON_DIR = PLUGIN_ROOT / "templates" / "section-skeletons"


def test_company_skeleton_has_the_expected_structure():
    text = (SKELETON_DIR / "companies.md").read_text(encoding="utf-8")
    for marker in (
        "### Company Overview",
        "### Unique Bullet Points",
        "**Company Name:**",
        "**Role Titles:**",
        "**Business Domain:**",
        "**Integrated Tech Stack:**",
    ):
        assert marker in text


def test_project_skeleton_has_the_expected_structure():
    text = (SKELETON_DIR / "projects.md").read_text(encoding="utf-8")
    for marker in (
        "### Project Overview",
        "### Unique Bullet Points",
        "**Project Name:**",
        "**Integrated Tech Stack:**",
    ):
        assert marker in text


def test_skeletons_are_not_scaffolded_into_the_workspace(tmp_path):
    """The skeletons live outside templates/workspace/, so init_workspace must not
    place them into companies/ or projects/ (which stay empty for the user)."""
    init_workspace(str(tmp_path))
    assert list((tmp_path / "private/resume_sections/companies").iterdir()) == []
    assert list((tmp_path / "private/resume_sections/projects").iterdir()) == []
