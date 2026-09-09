import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from scaffold_data import scaffold_data  # noqa: E402

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PLUGIN_ROOT / "tests" / "fixtures" / "resume_sections"


def test_scaffolds_both_files(tmp_path):
    result = scaffold_data(str(tmp_path), str(SOURCE_DIR))
    assert (tmp_path / "tmp" / "resume.data.json").is_file()
    assert (tmp_path / "tmp" / "cover_letter.data.json").is_file()
    assert result == {
        "resume": str(tmp_path / "tmp" / "resume.data.json"),
        "cover_letter": str(tmp_path / "tmp" / "cover_letter.data.json"),
    }


def test_name_contact_lang_density_from_profile(tmp_path):
    scaffold_data(str(tmp_path), str(SOURCE_DIR))
    resume = json.loads((tmp_path / "tmp" / "resume.data.json").read_text(encoding="utf-8"))
    assert resume["name"] == "Sample Dev"
    assert resume["lang"] == "en"
    assert resume["density"] == "compact"  # from profile.yml conventions.density
    assert resume["contact"] == [
        "(+00) 000-000-000",
        {"text": "sample.dev@example.com", "href": "mailto:sample.dev@example.com"},
        {"text": "github.com/sample-dev", "href": "https://github.com/sample-dev"},
    ]


def test_explicit_density_flag_overrides_profile(tmp_path):
    scaffold_data(str(tmp_path), str(SOURCE_DIR), density="standard")
    resume = json.loads((tmp_path / "tmp" / "resume.data.json").read_text(encoding="utf-8"))
    assert resume["density"] == "standard"


def test_experience_items_match_profile_roles_verbatim(tmp_path):
    scaffold_data(str(tmp_path), str(SOURCE_DIR))
    resume = json.loads((tmp_path / "tmp" / "resume.data.json").read_text(encoding="utf-8"))
    exp = next(s for s in resume["sections"] if s["type"] == "entries")
    assert exp["title"] == "Industrial Experience"
    assert [it["primary"] for it in exp["items"]] == ["Software Engineer", "Junior Developer"]
    assert exp["items"][0]["secondary"] == "Acme Corp"
    assert exp["items"][0]["dates"] == "Jan. 2024 – Present"
    assert exp["items"][0]["location"] == "Sydney, Australia"
    # Judgment fields are left for the model to fill in.
    assert exp["items"][0]["stack"] == ""
    assert exp["items"][0]["bullets"] == []


def test_education_section_fully_filled(tmp_path):
    scaffold_data(str(tmp_path), str(SOURCE_DIR))
    resume = json.loads((tmp_path / "tmp" / "resume.data.json").read_text(encoding="utf-8"))
    edu = next(s for s in resume["sections"] if s["type"] == "education")
    assert edu["items"] == [
        {
            "institution": "Example University",
            "dates": "2018 – 2021",
            "credential": "Bachelor of Computer Science",
            "location": "Sydney, Australia",
        }
    ]


def test_skills_and_intro_left_empty_for_model(tmp_path):
    scaffold_data(str(tmp_path), str(SOURCE_DIR))
    resume = json.loads((tmp_path / "tmp" / "resume.data.json").read_text(encoding="utf-8"))
    skills = next(s for s in resume["sections"] if s["type"] == "skills")
    assert skills["groups"] == []
    assert resume["intro"] == []
    assert "introTitle" not in resume  # only set for --lang zh


def test_cover_letter_prefilled_and_judgment_fields_empty(tmp_path):
    scaffold_data(str(tmp_path), str(SOURCE_DIR))
    cover = json.loads((tmp_path / "tmp" / "cover_letter.data.json").read_text(encoding="utf-8"))
    assert cover["name"] == "Sample Dev"
    assert cover["signature"] == "Sample Dev"
    assert cover["salutation"] == "Dear Hiring Manager,"
    assert cover["closing"] == "Sincerely,"
    assert cover["date"]  # today's date, some non-empty string
    assert cover["recipient"] == []
    assert cover["subject"] == ""
    assert cover["paragraphs"] == []


def test_zh_lang_sets_chinese_section_titles_and_intro_title(tmp_path):
    scaffold_data(str(tmp_path), str(SOURCE_DIR), lang="zh")
    resume = json.loads((tmp_path / "tmp" / "resume.data.json").read_text(encoding="utf-8"))
    titles = [s["title"] for s in resume["sections"]]
    assert titles == ["工作经验", "教育背景", "技能"]
    assert resume["introTitle"] == "简介"

    cover = json.loads((tmp_path / "tmp" / "cover_letter.data.json").read_text(encoding="utf-8"))
    # Chinese salutation/closing are the model's translation job, not scaffolded.
    assert cover["salutation"] == ""
    assert cover["closing"] == ""


def test_missing_profile_raises(tmp_path):
    empty_source = tmp_path / "empty_source"
    empty_source.mkdir()
    try:
        scaffold_data(str(tmp_path / "app"), str(empty_source))
        assert False, "expected FileNotFoundError"
    except FileNotFoundError as exc:
        assert "profile.yml" in str(exc)


def test_rerun_overwrites(tmp_path):
    scaffold_data(str(tmp_path), str(SOURCE_DIR), lang="en")
    scaffold_data(str(tmp_path), str(SOURCE_DIR), lang="zh")
    resume = json.loads((tmp_path / "tmp" / "resume.data.json").read_text(encoding="utf-8"))
    assert resume["lang"] == "zh"


def test_cli_writes_both_files(tmp_path):
    script = PLUGIN_ROOT / "scripts" / "scaffold_data.py"
    result = subprocess.run(
        [
            "uv", "run", "--project", str(PLUGIN_ROOT), str(script),
            "--dir", str(tmp_path), "--source-dir", str(SOURCE_DIR), "--lang", "en",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "resume.data.json" in result.stdout
    assert "cover_letter.data.json" in result.stdout
    assert (tmp_path / "tmp" / "resume.data.json").is_file()
