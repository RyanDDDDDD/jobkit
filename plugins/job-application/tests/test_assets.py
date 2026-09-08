from pathlib import Path

from jobkit import __version__
from jobkit._assets import resource_text, template_path, templates_dir


def test_version_is_060():
    assert __version__ == "0.6.0"


def test_reference_docs_are_bundled():
    for name in ("workflow-rules", "render-contract", "output-layout",
                 "ats-checklist", "interview-frameworks"):
        text = resource_text(f"reference/{name}.md")
        assert text.strip(), name


def test_templates_are_bundled():
    for kind in ("resume", "cover_letter"):
        p = template_path(kind)
        assert p.is_file()
        assert "{{DATA_JSON}}" in p.read_text(encoding="utf-8")


def test_templates_dir_has_workspace_and_fonts():
    d = templates_dir()
    assert (d / "workspace").is_dir()
    assert (d / "fonts").is_dir()
    assert (d / "section-skeletons").is_dir()
