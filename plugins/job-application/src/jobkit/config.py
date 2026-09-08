"""Resolve jobapp.config.yml settings, walking up from the current directory
for the file, merged over the plugin's defaults.

CLI: jobkit config [--json]
prints the resolved config as JSON to stdout.
"""
import json
import os
from pathlib import Path

import yaml


def get_job_app_config() -> dict:
    cfg = {
        "root": str(Path.cwd()),
        "browser_path": None,
        "source_of_truth_dir": "resume_sections",
        "output_dir": "applications/{Company}",
        "interview_playbook": "interview_playbook.md",
    }
    directory = Path.cwd()
    while True:
        candidate = directory / "jobapp.config.yml"
        if candidate.is_file():
            cfg["root"] = str(directory)
            data = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
            if data.get("browser_path"):
                cfg["browser_path"] = os.path.expandvars(data["browser_path"])
            if data.get("source_of_truth_dir"):
                cfg["source_of_truth_dir"] = data["source_of_truth_dir"]
            if data.get("output_dir"):
                cfg["output_dir"] = data["output_dir"]
            if data.get("interview_playbook"):
                cfg["interview_playbook"] = data["interview_playbook"]
            break
        parent = directory.parent
        if parent == directory:
            break
        directory = parent
    return cfg


if __name__ == "__main__":
    print(json.dumps(get_job_app_config()))
