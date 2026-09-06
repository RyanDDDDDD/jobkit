import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from init_workspace import init_workspace  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
FRAMEWORKS = PLUGIN_ROOT / "reference" / "interview-frameworks.md"

EXPECTED_FILES = {
    "jobapp.config.yml",
    "CLAUDE.md",
    "private/questions_to_ask.md",
    "private/interview_playbook.md",
    "private/resume_sections/profile.yml",
    "private/resume_sections/factual-bounds.md",
    "private/resume_sections/introduction.md",
    "private/resume_sections/skills.md",
    "private/resume_sections/education.md",
}
EXPECTED_DIRS = (
    "applications",
    "private/resume_sections/companies",
    "private/resume_sections/projects",
)


def _digests(root: Path) -> dict:
    return {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_fresh_workspace_creates_every_file_and_dir(tmp_path):
    result = init_workspace(str(tmp_path))
    assert set(result["created"]) == EXPECTED_FILES
    assert result["skipped"] == []
    for rel in EXPECTED_FILES:
        assert (tmp_path / rel).is_file()
    for rel in EXPECTED_DIRS:
        assert (tmp_path / rel).is_dir()


def test_created_list_is_sorted(tmp_path):
    result = init_workspace(str(tmp_path))
    assert result["created"] == sorted(result["created"])


def test_config_has_private_layout(tmp_path):
    init_workspace(str(tmp_path))
    cfg = (tmp_path / "jobapp.config.yml").read_text(encoding="utf-8")
    assert 'source_of_truth_dir: "private/resume_sections"' in cfg
    assert 'output_dir: "applications/{Company}"' in cfg
    assert 'interview_playbook: "private/interview_playbook.md"' in cfg


def test_playbook_seeded_byte_identical_to_frameworks(tmp_path):
    init_workspace(str(tmp_path))
    assert (tmp_path / "private" / "interview_playbook.md").read_bytes() == FRAMEWORKS.read_bytes()


def test_skills_template_keeps_category_headers(tmp_path):
    init_workspace(str(tmp_path))
    skills = (tmp_path / "private/resume_sections/skills.md").read_text(encoding="utf-8")
    for header in (
        "### Core Languages",
        "### Frameworks & Libraries",
        "### Tools, DevOps & Cloud",
        "### Concepts, Protocols & Data",
    ):
        assert header in skills


def test_profile_template_has_todo_markers(tmp_path):
    init_workspace(str(tmp_path))
    profile = (tmp_path / "private/resume_sections/profile.yml").read_text(encoding="utf-8")
    assert "# TODO" in profile


def test_profile_template_uses_flat_convention_keys(tmp_path):
    init_workspace(str(tmp_path))
    profile = (tmp_path / "private/resume_sections/profile.yml").read_text(encoding="utf-8")
    assert "density:" in profile
    assert "include_projects:" in profile
    assert "default_density" not in profile
    assert "default_resume_length" not in profile
    assert "default_include_projects" not in profile


def test_no_warnings_on_clean_fresh_dir(tmp_path):
    result = init_workspace(str(tmp_path))
    assert result["warnings"] == []


def test_warns_on_preexisting_flat_resume_sections(tmp_path):
    (tmp_path / "resume_sections").mkdir()
    result = init_workspace(str(tmp_path))
    assert result["warnings"]
    assert any("resume_sections" in w and "private/" in w for w in result["warnings"])


def test_no_warning_when_config_already_present(tmp_path):
    (tmp_path / "jobapp.config.yml").write_text("# my custom config\n", encoding="utf-8")
    (tmp_path / "resume_sections").mkdir()
    result = init_workspace(str(tmp_path))
    assert result["warnings"] == []


def test_rerun_is_idempotent_and_mutates_nothing(tmp_path):
    init_workspace(str(tmp_path))
    before = _digests(tmp_path)
    result = init_workspace(str(tmp_path))
    assert result["created"] == []
    assert set(result["skipped"]) == EXPECTED_FILES
    assert _digests(tmp_path) == before


def test_existing_file_is_never_clobbered(tmp_path):
    (tmp_path / "jobapp.config.yml").write_text("# my custom config\n", encoding="utf-8")
    result = init_workspace(str(tmp_path))
    assert "jobapp.config.yml" in result["skipped"]
    assert "jobapp.config.yml" not in result["created"]
    assert (tmp_path / "jobapp.config.yml").read_text(encoding="utf-8") == "# my custom config\n"
    assert (tmp_path / "CLAUDE.md").is_file()  # the rest still scaffolds


def test_explicit_target_arg_scaffolds_there_not_cwd(tmp_path):
    sub = tmp_path / "nested" / "ws"
    init_workspace(str(sub))
    assert (sub / "jobapp.config.yml").is_file()
    assert not (tmp_path / "jobapp.config.yml").exists()


def test_cli_json_output(tmp_path):
    script = PLUGIN_ROOT / "scripts" / "init_workspace.py"
    result = subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), str(script), str(tmp_path), "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    parsed = json.loads(result.stdout)
    assert set(parsed["created"]) == EXPECTED_FILES


def test_cli_text_output_mentions_next_steps(tmp_path):
    script = PLUGIN_ROOT / "scripts" / "init_workspace.py"
    result = subprocess.run(
        ["uv", "run", "--project", str(PLUGIN_ROOT), str(script), str(tmp_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "created" in result.stdout
    assert "profile.yml" in result.stdout
    assert "/job-application:apply" in result.stdout
