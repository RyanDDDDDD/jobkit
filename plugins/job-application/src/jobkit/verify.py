"""Deterministic checks over a rendered job application, for apply's self-check.

Reads the two data.json files, the two rendered PDFs, cover_letter.txt and
profile.yml; runs mechanical checks that need no LLM. Prints a human summary, or
--json: {"pass": [...], "fail": [{"id","detail"}], "warn": [{"id","detail"}]}.

Exit 0 for any check outcome (the report is advisory, not a gate); exit 1 only
on a missing required input.

CLI: jobkit verify --dir <appdir> --source-dir <sourceDir> [--json]
"""
import argparse
import difflib
import json
import sys
import tempfile
from pathlib import Path

import pymupdf
import yaml

from jobkit.cover_txt import cover_letter_to_text
from jobkit.extract_cv import extract_text

# Ligature clusters and a leading "+" do not survive text extraction on the
# bundled fonts (see reference/render-contract.md) -- skip any assertion whose
# expected string contains one.
_LIGATURES = ("ffi", "ffl", "fi", "fl", "ff", "ft")


def _extractable(s: str) -> bool:
    return bool(s) and not s.startswith("+") and not any(l in s for l in _LIGATURES)


def _en_dash_range(start: str, end: str) -> str:
    return f"{start} – {end}"


def check_profile_roles(resume: dict, profile: dict) -> list[str]:
    roles = ((profile.get("conventions") or {}).get("roles")) or []
    want = {
        (r.get("title", ""), r.get("company", ""), r.get("location", ""),
         _en_dash_range(r.get("start", ""), r.get("end", "")))
        for r in roles
    }
    fails = []
    for sec in resume.get("sections", []):
        if sec.get("type") != "entries":
            continue
        for it in sec.get("items", []):
            if "dates" not in it:  # a Selected Projects item, not a role
                continue
            got = (it.get("primary", ""), it.get("secondary", ""),
                   it.get("location", ""), it.get("dates", ""))
            if got not in want:
                fails.append(
                    f"experience item {got!r} matches no profile.yml "
                    f"conventions.roles entry verbatim"
                )
    return fails


def check_profile_education(resume: dict, profile: dict) -> list[str]:
    edu = ((profile.get("conventions") or {}).get("education")) or []
    want = {
        (e.get("institution", ""), e.get("credential", ""), e.get("location", ""),
         _en_dash_range(e.get("start", ""), e.get("end", "")))
        for e in edu
    }
    fails = []
    for sec in resume.get("sections", []):
        if sec.get("type") != "education":
            continue
        for it in sec.get("items", []):
            got = (it.get("institution", ""), it.get("credential", ""),
                   it.get("location", ""), it.get("dates", ""))
            if got not in want:
                fails.append(
                    f"education item {got!r} matches no conventions.education entry verbatim"
                )
    return fails


def _iter_dates(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "dates" and isinstance(v, str):
                yield v
            else:
                yield from _iter_dates(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_dates(v)


def check_date_format(resume: dict, cover: dict) -> list[str]:
    fails = []
    for d in list(_iter_dates(resume)) + list(_iter_dates(cover)):
        if " – " not in d or "--" in d or " - " in d:
            fails.append(
                f"dates string {d!r} is not '<start> – <end>' "
                f"(space, U+2013 en-dash, space)"
            )
    return fails


def check_cover_txt_fresh(cover_data_path: Path, cover_txt_path: Path) -> list[str]:
    if not cover_txt_path.is_file():
        return ["cover_letter.txt is missing"]
    on_disk = cover_txt_path.read_text(encoding="utf-8")
    fails = []
    with tempfile.TemporaryDirectory() as td:
        fresh = cover_letter_to_text(str(cover_data_path), str(Path(td) / "cl.txt"))
    if fresh != on_disk:
        fails.append(
            "cover_letter.txt is stale — it differs from a fresh regeneration "
            "from cover_letter.data.json"
        )
    first = on_disk.splitlines()[0] if on_disk.splitlines() else ""
    if not (first.startswith("Subject:") or first.startswith("主题：")):
        fails.append(f"cover_letter.txt first line is not a Subject line: {first!r}")
    return fails


def _all_bullets(resume: dict, cover: dict) -> list[tuple[str, str]]:
    out = []
    for sec in resume.get("sections", []):
        for it in sec.get("items", []):
            for b in it.get("bullets", []) or []:
                out.append(("resume", str(b)))
    for p in cover.get("paragraphs", []) or []:
        out.append(("cover", str(p)))
    return out


def _norm(s: str) -> str:
    return " ".join(s.lower().strip().lstrip("-").split())


def check_bullet_dupes(resume: dict, cover: dict) -> list[str]:
    items = _all_bullets(resume, cover)
    warns = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            ratio = difflib.SequenceMatcher(None, _norm(items[i][1]), _norm(items[j][1])).ratio()
            if ratio >= 0.85:
                warns.append(
                    f"{items[i][0]} text ~ {items[j][0]} text ({ratio:.2f}): "
                    f"{items[i][1][:60]!r} / {items[j][1][:60]!r}"
                )
    return warns


def check_resume_roundtrip(resume: dict, resume_pdf: Path) -> list[str]:
    text = extract_text(str(resume_pdf))
    fails = []
    if "Invalid resume JSON" in text:
        fails.append("resume.pdf renders the 'Invalid resume JSON' error page")
    name = resume.get("name", "")
    if _extractable(name) and name not in text:
        fails.append(f"resume.pdf extracted text is missing the candidate name {name!r}")
    companies = [
        it.get("secondary", "")
        for sec in resume.get("sections", []) if sec.get("type") == "entries"
        for it in sec.get("items", []) if "dates" in it
    ]
    checkable = [c for c in companies if _extractable(c)]
    if checkable and not any(c in text for c in checkable):
        fails.append(f"resume.pdf extracted text contains none of the company names {checkable!r}")
    return fails


def check_cover_roundtrip(cover: dict, cover_pdf: Path) -> list[str]:
    text = extract_text(str(cover_pdf))
    fails = []
    if "Invalid cover letter JSON" in text:
        fails.append("cover_letter.pdf renders the 'Invalid cover letter JSON' error page")
    name = cover.get("name", "")
    if _extractable(name) and name not in text:
        fails.append(f"cover_letter.pdf extracted text is missing the name {name!r}")
    subject = cover.get("subject", "")
    if _extractable(subject) and subject not in text:
        fails.append(f"cover_letter.pdf extracted text is missing the subject {subject!r}")
    return fails


def check_page_budget(resume_pdf: Path, cover_pdf: Path) -> list[str]:
    fails = []
    with pymupdf.open(str(resume_pdf)) as d:
        if len(d) > 2:
            fails.append(f"resume.pdf is {len(d)} pages (soft ceiling 2)")
    with pymupdf.open(str(cover_pdf)) as d:
        if len(d) != 1:
            fails.append(f"cover_letter.pdf is {len(d)} pages (expected 1)")
    return fails


def verify(app_dir: str, source_dir: str) -> dict:
    app = Path(app_dir).resolve()
    src = Path(source_dir).resolve()
    resume_data = app / "tmp" / "resume.data.json"
    cover_data = app / "tmp" / "cover_letter.data.json"
    resume_pdf = app / "resume.pdf"
    cover_pdf = app / "cover_letter.pdf"
    cover_txt = app / "cover_letter.txt"
    profile_path = src / "profile.yml"

    for required in (resume_data, cover_data, resume_pdf, cover_pdf, profile_path):
        if not required.is_file():
            raise FileNotFoundError(f"missing required input: {required}")

    resume = json.loads(resume_data.read_text(encoding="utf-8"))
    cover = json.loads(cover_data.read_text(encoding="utf-8"))
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}

    fail_checks = {
        "profile-roles-verbatim": check_profile_roles(resume, profile),
        "profile-education-verbatim": check_profile_education(resume, profile),
        "resume-roundtrip": check_resume_roundtrip(resume, resume_pdf),
        "cover-roundtrip": check_cover_roundtrip(cover, cover_pdf),
        "page-budget": check_page_budget(resume_pdf, cover_pdf),
        "cover-txt-fresh": check_cover_txt_fresh(cover_data, cover_txt),
        "date-format": check_date_format(resume, cover),
    }
    warn_checks = {"bullet-dupes": check_bullet_dupes(resume, cover)}

    result = {"pass": [], "fail": [], "warn": []}
    for cid, msgs in fail_checks.items():
        if msgs:
            result["fail"] += [{"id": cid, "detail": m} for m in msgs]
        else:
            result["pass"].append(cid)
    for cid, msgs in warn_checks.items():
        if msgs:
            result["warn"] += [{"id": cid, "detail": m} for m in msgs]
        else:
            result["pass"].append(cid)
    return result


def _format(result: dict) -> str:
    lines = []
    for cid in result["pass"]:
        lines.append(f"  pass   {cid}")
    for e in result["warn"]:
        lines.append(f"  warn   {e['id']}: {e['detail']}")
    for e in result["fail"]:
        lines.append(f"  FAIL   {e['id']}: {e['detail']}")
    if not result["fail"] and not result["warn"]:
        lines.append("\nAll deterministic checks passed.")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = verify(args.dir, args.source_dir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result) if args.json else _format(result))


if __name__ == "__main__":
    main()
