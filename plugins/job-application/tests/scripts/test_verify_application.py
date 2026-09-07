import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from verify_application import (  # noqa: E402
    check_bullet_dupes,
    check_cover_txt_fresh,
    check_date_format,
    check_profile_education,
    check_profile_roles,
)

REPO = Path(__file__).resolve().parents[2]

PROFILE = {
    "conventions": {
        "roles": [
            {"company": "Acme Corp", "title": "Software Engineer",
             "start": "Jan. 2024", "end": "Present", "location": "Sydney, Australia"},
        ],
        "education": [
            {"institution": "Example University", "credential": "BCS",
             "start": "2018", "end": "2021", "location": "Sydney, Australia"},
        ],
    }
}


def _resume(dates="Jan. 2024 – Present", company="Acme Corp"):
    return {
        "name": "Sample Dev",
        "sections": [
            {"title": "Experience", "type": "entries", "items": [
                {"primary": "Software Engineer", "secondary": company,
                 "location": "Sydney, Australia", "dates": dates,
                 "bullets": ["Built a REST API for carrier integration."]},
            ]},
            {"title": "Education", "type": "education", "items": [
                {"institution": "Example University", "credential": "BCS",
                 "location": "Sydney, Australia", "dates": "2018 – 2021"},
            ]},
        ],
    }


def _cover(paragraphs=None):
    return {
        "name": "Sample Dev", "lang": "en",
        "subject": "Application for the Position of Integration Developer",
        "paragraphs": paragraphs or ["I am writing to apply for the role."],
        "closing": "Sincerely,", "signature": "Sample Dev",
    }


def test_clean_resume_passes_role_and_education_checks():
    assert check_profile_roles(_resume(), PROFILE) == []
    assert check_profile_education(_resume(), PROFILE) == []


def test_role_dates_with_hyphen_fail_date_format():
    bad = _resume(dates="Jan. 2024 - Present")
    assert check_date_format(bad, _cover()) != []


def test_wrong_company_fails_profile_roles():
    bad = _resume(company="Acme Corporation")
    fails = check_profile_roles(bad, PROFILE)
    assert fails and "Acme Corporation" in fails[0]


def test_stale_cover_txt_is_flagged(tmp_path):
    cd = tmp_path / "cover_letter.data.json"
    cd.write_text(json.dumps(_cover()), encoding="utf-8")
    txt = tmp_path / "cover_letter.txt"
    txt.write_text("Subject: something totally different\n", encoding="utf-8")
    fails = check_cover_txt_fresh(cd, txt)
    assert any("stale" in f for f in fails)


def test_fresh_cover_txt_passes(tmp_path):
    from cover_letter_to_txt import cover_letter_to_text
    cd = tmp_path / "cover_letter.data.json"
    cd.write_text(json.dumps(_cover()), encoding="utf-8")
    txt = tmp_path / "cover_letter.txt"
    cover_letter_to_text(str(cd), str(txt))
    assert check_cover_txt_fresh(cd, txt) == []


def test_near_duplicate_bullets_warn():
    r = _resume()
    r["sections"][0]["items"][0]["bullets"] = [
        "Built a REST API for carrier integration.",
        "Built a REST API for carrier integrations.",
    ]
    assert check_bullet_dupes(r, _cover()) != []


def test_missing_input_exits_1(tmp_path):
    script = REPO / "scripts" / "verify_application.py"
    result = subprocess.run(
        ["uv", "run", "--project", str(REPO), str(script),
         "--dir", str(tmp_path), "--source-dir", str(tmp_path), "--json"],
        capture_output=True, text=True,
    )
    assert result.returncode == 1
