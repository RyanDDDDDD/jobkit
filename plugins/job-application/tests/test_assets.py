from pathlib import Path

from jobkit import __version__
from jobkit._assets import resource_text, template_path, templates_dir


def test_version_is_080():
    assert __version__ == "0.8.0"


def test_reference_docs_are_bundled():
    for name in ("workflow-rules", "render-contract", "output-layout",
                 "ats-checklist", "interview-frameworks"):
        text = resource_text(f"reference/{name}.md")
        assert text.strip(), name


def test_templates_are_bundled():
    from jobkit._assets import RESUME_TEMPLATES
    for theme in RESUME_TEMPLATES:
        for kind in ("resume", "cover_letter"):
            p = template_path(kind, theme)
            assert p.is_file(), (theme, kind)
            assert "{{DATA_JSON}}" in p.read_text(encoding="utf-8")


def test_templates_dir_has_workspace_and_fonts():
    d = templates_dir()
    assert (d / "workspace").is_dir()
    assert (d / "fonts").is_dir()
    assert (d / "section-skeletons").is_dir()
    for name in (
        "Newsreader.woff2",
        "SourceSerif4.woff2",
        "SourceSans3.woff2",
        "NotoSansSC.woff2",
        "OFL.txt",
    ):
        assert (d / "fonts" / name).is_file(), name


def test_resolve_template_prefers_workspace_override(tmp_path):
    from jobkit._assets import resolve_template_path
    override_dir = tmp_path / "templates"
    override_dir.mkdir()
    override = override_dir / "resume.html"
    override.write_text("{{DATA_JSON}}", encoding="utf-8")
    assert resolve_template_path("resume", root=tmp_path) == override
    bundled = template_path("resume", "dossier")
    assert resolve_template_path("resume", theme="classic") == template_path("resume", "classic")
    assert resolve_template_path("resume", theme="dossier", explicit=str(bundled)) == bundled
