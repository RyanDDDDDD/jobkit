"""Every subcommand invoked for real via `python -m jobkit`, asserting the
exit code and first stdout line match the pre-refactor scripts."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

FIX = Path(__file__).resolve().parent / "fixtures"


def run(*args, cwd=None):
    return subprocess.run([sys.executable, "-m", "jobkit", *args],
                          capture_output=True, text=True, cwd=cwd)


def test_version():
    assert run("--version").stdout.strip() == "jobkit 0.6.0"


def test_config_prints_json(tmp_path):
    r = run("config", cwd=tmp_path)
    assert r.returncode == 0
    cfg = json.loads(r.stdout)
    assert cfg["source_of_truth_dir"] == "resume_sections"
    assert cfg["root"] == str(tmp_path)


def test_config_walks_up_for_jobapp_yml(tmp_path):
    (tmp_path / "jobapp.config.yml").write_text(
        'output_dir: "custom/{Company}"\n', encoding="utf-8")
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    cfg = json.loads(run("config", cwd=sub).stdout)
    assert cfg["root"] == str(tmp_path)
    assert cfg["output_dir"] == "custom/{Company}"


def test_extract_cv_reads_markdown(tmp_path):
    p = tmp_path / "cv.md"
    p.write_text("# Jane\nPython, SQL\n", encoding="utf-8")
    r = run("extract-cv", str(p))
    assert r.returncode == 0
    assert "Jane" in r.stdout


def test_extract_cv_unsupported_type_exits_2(tmp_path):
    p = tmp_path / "cv.rtf"
    p.write_text("x", encoding="utf-8")
    assert run("extract-cv", str(p)).returncode == 2


def test_init_scaffolds(tmp_path):
    r = run("init", str(tmp_path), "--json")
    assert r.returncode == 0
    result = json.loads(r.stdout)
    assert "jobapp.config.yml" in result["created"]
    assert (tmp_path / "private/resume_sections/profile.yml").is_file()
    assert (tmp_path / "private/interview_playbook.md").is_file()


def test_doc_prints_markdown():
    r = run("doc", "workflow-rules")
    assert r.returncode == 0
    assert r.stdout.lstrip().startswith("#")


def test_render_flag_count_mismatch_exits_2(tmp_path):
    r = run("render", "--kind", "resume", "--kind", "cover_letter",
            "--data", "a.json", "--out", "a.pdf")
    assert r.returncode == 2
    assert "same number of times" in r.stderr


def test_verify_missing_input_exits_1(tmp_path):
    r = run("verify", "--dir", str(tmp_path), "--source-dir", str(tmp_path))
    assert r.returncode == 1


@pytest.mark.parametrize("kind", ["resume", "cover_letter"])
def test_render_uses_bundled_template(tmp_path, kind, chromium_or_skip):
    data = {
        "resume": '{"name":"T","contact":["x@e.com"],"sections":['
                  '{"title":"Skills","type":"skills","groups":['
                  '{"label":"L","value":"Python"}]}]}',
        "cover_letter": '{"name":"T","subject":"Application for the Position of X",'
                        '"salutation":"Dear Hiring Manager,","paragraphs":["Hi."],'
                        '"closing":"Sincerely,","signature":"T"}',
    }[kind]
    d = tmp_path / "d.json"; d.write_text(data, encoding="utf-8")
    out = tmp_path / "o.pdf"
    r = run("render", "--kind", kind, "--data", str(d), "--out", str(out))
    assert r.returncode == 0, r.stderr
    assert r.stdout.startswith("OK:")
    assert out.is_file()
