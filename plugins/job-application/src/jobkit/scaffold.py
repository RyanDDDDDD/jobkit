"""Scaffold resume.data.json and cover_letter.data.json from profile.yml.

Pre-fills every field that `profile.yml` (plus --lang/--density) already
determines -- name, contact, lang, density, today's date, each Experience
item's primary/dates/secondary/location, and the full Education section --
so the apply skill never hand-retypes them. Judgment fields (intro, bullets,
stack, skills groups, Selected Projects, cover-letter recipient/subject/
paragraphs) are left empty for the model to fill in afterwards with Edit.

Always overwrites both files.

CLI: jobkit scaffold-data --dir <appdir> --source-dir <sourceDir> [--lang en|zh] [--density compact|standard]
"""
import argparse
import json
import re
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


_ZH_MONTHS = {
    "Jan": "1", "Feb": "2", "Mar": "3", "Apr": "4", "May": "5", "Jun": "6",
    "Jul": "7", "Aug": "8", "Sep": "9", "Oct": "10", "Nov": "11", "Dec": "12",
}


def _zh_date_token(token: str) -> str:
    """Reformat one date token for --lang zh. Unrecognized formats pass through
    verbatim rather than risk a wrong guess."""
    token = token.strip()
    if token == "Present":
        return "至今"
    m = re.match(r"^([A-Za-z]{3})\.?\s+(\d{4})$", token)
    if m:
        mon, year = m.groups()
        mon_zh = _ZH_MONTHS.get(mon.capitalize())
        if mon_zh:
            return f"{year}年{mon_zh}月"
    if re.match(r"^\d{4}$", token):
        return f"{token}年"
    return token


def _dates(entry: dict, lang: str = "en") -> str:
    start = entry.get("start", "")
    end = entry.get("end", "")
    if lang == "zh":
        start = _zh_date_token(start)
        end = _zh_date_token(end)
    return f"{start} – {end}"


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
    experience_items = []
    for r in roles:
        company = r.get("company", "")
        ticker = r.get("ticker", "")
        secondary = f"{company} ({ticker})" if ticker else company
        experience_items.append({
            "primary": r.get("title", ""),
            "dates": _dates(r, lang),
            "secondary": secondary,
            "location": r.get("location", ""),
            "stack": "",
            "bullets": [],
        })

    education = ((profile.get("conventions") or {}).get("education")) or []
    include_gpa = bool(((profile.get("conventions") or {}).get("include_gpa")))
    education_items = []
    for e in education:
        item = {
            "institution": e.get("institution", ""),
            "dates": _dates(e, lang),
            "credential": e.get("credential", ""),
            "location": e.get("location", ""),
        }
        if e.get("rank"):
            item["note"] = e["rank"]
        if include_gpa and e.get("gpa"):
            item["gpa"] = e["gpa"]
        education_items.append(item)

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
