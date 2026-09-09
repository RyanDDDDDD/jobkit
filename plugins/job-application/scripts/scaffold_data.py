"""Scaffold resume.data.json and cover_letter.data.json from profile.yml.

Pre-fills every field that `profile.yml` (plus --lang/--density) already
determines -- name, contact, lang, density, today's date, each Experience
item's primary/dates/secondary/location, and the full Education section --
so the apply skill never hand-retypes them. Judgment fields (intro, bullets,
stack, skills groups, Selected Projects, cover-letter recipient/subject/
paragraphs) are left empty for the model to fill in afterwards with Edit.

Always overwrites both files.

CLI: uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/scaffold_data.py \
        --dir <appdir> --source-dir <sourceDir> [--lang en|zh] [--density compact|standard]
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

SECTION_TITLES = {
    "en": {"experience": "Industrial Experience", "education": "Education", "skills": "Skills"},
    "zh": {"experience": "工作经验", "education": "教育背景", "skills": "技能"},
}


def _contact(profile: dict) -> list:
    contact = [profile.get("phone", "")]
    email = profile.get("email", "")
    contact.append({"text": email, "href": f"mailto:{email}"})
    github = (profile.get("links") or {}).get("github")
    if github:
        contact.append({"text": f"github.com/{github}", "href": f"https://github.com/{github}"})
    return contact


def _dates(entry: dict) -> str:
    return f"{entry.get('start', '')} – {entry.get('end', '')}"


def _resolve_density(profile: dict, density: str | None) -> str:
    if density:
        return density
    return ((profile.get("conventions") or {}).get("density")) or "compact"


def _today_long() -> str:
    today = date.today()
    return f"{today:%B} {today.day}, {today.year}"


def scaffold_data(app_dir: str, source_dir: str, lang: str = "en", density: str | None = None) -> dict:
    """Write resume.data.json and cover_letter.data.json into {app_dir}/tmp/.

    Returns {"resume": <path>, "cover_letter": <path>}.
    """
    app = Path(app_dir).resolve()
    src = Path(source_dir).resolve()
    profile_path = src / "profile.yml"
    if not profile_path.is_file():
        raise FileNotFoundError(f"missing required input: {profile_path}")
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}

    tmp = app / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)

    titles = SECTION_TITLES[lang]
    name = profile.get("name", "")
    contact = _contact(profile)
    resolved_density = _resolve_density(profile, density)

    roles = ((profile.get("conventions") or {}).get("roles")) or []
    experience_items = [
        {
            "primary": r.get("title", ""),
            "dates": _dates(r),
            "secondary": r.get("company", ""),
            "location": r.get("location", ""),
            "stack": "",
            "bullets": [],
        }
        for r in roles
    ]

    education = ((profile.get("conventions") or {}).get("education")) or []
    education_items = [
        {
            "institution": e.get("institution", ""),
            "dates": _dates(e),
            "credential": e.get("credential", ""),
            "location": e.get("location", ""),
        }
        for e in education
    ]

    resume = {
        "name": name,
        "lang": lang,
        "density": resolved_density,
        "contact": contact,
    }
    if lang == "zh":
        resume["introTitle"] = "简介"
    resume["intro"] = []
    resume["sections"] = [
        {"title": titles["experience"], "type": "entries", "items": experience_items},
        {"title": titles["education"], "type": "education", "items": education_items},
        {"title": titles["skills"], "type": "skills", "groups": []},
    ]

    cover_letter = {
        "name": name,
        "lang": lang,
        "contact": contact,
        "date": _today_long(),
        "recipient": [],
        "subject": "",
        "salutation": "Dear Hiring Manager," if lang == "en" else "",
        "paragraphs": [],
        "closing": "Sincerely," if lang == "en" else "",
        "signature": name,
    }

    resume_path = tmp / "resume.data.json"
    cover_path = tmp / "cover_letter.data.json"
    resume_path.write_text(json.dumps(resume, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    cover_path.write_text(json.dumps(cover_letter, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {"resume": str(resume_path), "cover_letter": str(cover_path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--lang", default="en", choices=["en", "zh"])
    parser.add_argument("--density", choices=["compact", "standard"])
    args = parser.parse_args()
    try:
        result = scaffold_data(args.dir, args.source_dir, args.lang, args.density)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(f"Wrote {result['resume']}")
    print(f"Wrote {result['cover_letter']}")


if __name__ == "__main__":
    main()
