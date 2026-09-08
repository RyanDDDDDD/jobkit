import json
import subprocess
import sys
from pathlib import Path

import pytest

from jobkit.config import get_job_app_config


def test_no_config_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = get_job_app_config()
    assert cfg["source_of_truth_dir"] == "resume_sections"
    assert cfg["output_dir"] == "applications/{Company}"
    assert cfg["interview_playbook"] == "interview_playbook.md"
    assert cfg["root"] == str(tmp_path)
    assert cfg["browser_path"] is None


def test_output_dir_override_wins(tmp_path, monkeypatch):
    (tmp_path / "jobapp.config.yml").write_text(
        '# test config\noutput_dir: "custom/{Company}"\n', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    cfg = get_job_app_config()
    assert cfg["output_dir"] == "custom/{Company}"
    assert cfg["source_of_truth_dir"] == "resume_sections"
    assert cfg["root"] == str(tmp_path)


def test_interview_playbook_override_wins(tmp_path, monkeypatch):
    (tmp_path / "jobapp.config.yml").write_text(
        'interview_playbook: "private/interview_playbook.md"\n', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    cfg = get_job_app_config()
    assert cfg["interview_playbook"] == "private/interview_playbook.md"
    assert cfg["source_of_truth_dir"] == "resume_sections"
    assert cfg["root"] == str(tmp_path)


def test_config_found_by_walking_up_from_subdirectory(tmp_path, monkeypatch):
    (tmp_path / "jobapp.config.yml").write_text(
        'output_dir: "custom/{Company}"\n', encoding="utf-8"
    )
    nested = tmp_path / "applications" / "Acme"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)
    cfg = get_job_app_config()
    assert cfg["root"] == str(tmp_path)
    assert cfg["output_dir"] == "custom/{Company}"


def test_browser_path_is_read_and_env_expanded(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBAPP_TEST_DIR", "C:/does/not/exist")
    (tmp_path / "jobapp.config.yml").write_text(
        'browser_path: "$JOBAPP_TEST_DIR/msedge.exe"\n', encoding="utf-8"
    )
    monkeypatch.chdir(tmp_path)
    cfg = get_job_app_config()
    assert cfg["browser_path"] == "C:/does/not/exist/msedge.exe"


def test_cli_prints_valid_json(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "jobkit", "config", "--json"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    parsed = json.loads(result.stdout)
    assert parsed["source_of_truth_dir"] == "resume_sections"
    assert parsed["interview_playbook"] == "interview_playbook.md"
