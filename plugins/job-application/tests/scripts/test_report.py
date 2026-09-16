import json

from jobkit.render import RenderJob, RenderResult
from jobkit.report import (
    _analysis_gaps,
    _experience_order,
    _has_selected_projects,
    build_report,
)


def _resume(with_projects=False):
    sections = [
        {"title": "Experience", "type": "entries", "items": [
            {"primary": "Software Engineer", "secondary": "Acme Corp",
             "dates": "Jan. 2024 – Present"},
            {"primary": "Junior Developer", "secondary": "Globex Pty Ltd",
             "dates": "Feb. 2022 – Dec. 2023"},
        ]},
    ]
    if with_projects:
        sections.append({"title": "Selected Projects", "type": "entries", "items": [
            {"primary": "Side Project", "metaRight": "Python"},
        ]})
    return {"name": "Sample Dev", "lang": "en", "density": "compact", "sections": sections}


def test_has_selected_projects_true_when_titled_section_present():
    assert _has_selected_projects(_resume(with_projects=True)) is True


def test_has_selected_projects_false_without_it():
    assert _has_selected_projects(_resume()) is False


def test_experience_order_skips_selected_projects_section():
    order = _experience_order(_resume(with_projects=True))
    assert order == ["Acme Corp", "Globex Pty Ltd"]


def test_experience_order_empty_when_no_dated_entries():
    assert _experience_order({"sections": []}) == []


def test_analysis_gaps_extracts_only_gap_rows(tmp_path):
    analysis = tmp_path / "analysis.md"
    analysis.write_text(
        "## Criteria → Evidence\n"
        "| Criterion | Evidence (file:line) | Status |\n"
        "|---|---|---|\n"
        "| RESTful APIs | companies/acme.md:11 | met |\n"
        "| HL7 v2 / FHIR healthcare-interoperability standards | — | gap |\n"
        "\n"
        "## Fit\n"
        "stretch — has systems-integration experience.\n",
        encoding="utf-8",
    )
    assert _analysis_gaps(analysis) == [
        "HL7 v2 / FHIR healthcare-interoperability standards"
    ]


def test_analysis_gaps_missing_file_returns_empty(tmp_path):
    assert _analysis_gaps(tmp_path / "nope.md") == []


def test_build_report_all_success(tmp_path):
    (tmp_path / "tmp").mkdir()
    resume_data = tmp_path / "tmp" / "resume.data.json"
    resume_data.write_text(json.dumps(_resume()), encoding="utf-8")
    cover_data = tmp_path / "tmp" / "cover_letter.data.json"
    cover_data.write_text(json.dumps({"name": "Sample Dev", "lang": "en"}), encoding="utf-8")
    (tmp_path / "analysis.md").write_text(
        "## Criteria → Evidence\n| C | E | Status |\n|---|---|---|\n| X | — | gap |\n",
        encoding="utf-8",
    )
    jobs = [
        RenderJob("t1.html", str(resume_data), str(tmp_path / "resume.pdf")),
        RenderJob("t2.html", str(cover_data), str(tmp_path / "cover_letter.pdf")),
    ]
    results = [
        RenderResult(pdf=str(tmp_path / "resume.pdf"), pages=1, ok=True, log="", html=None),
        RenderResult(pdf=str(tmp_path / "cover_letter.pdf"), pages=1, ok=True, log="", html=None),
    ]
    report = build_report(jobs, results)
    assert "resume.pdf: OK, 1 page (lang=en, density=compact)" in report
    assert "cover_letter.pdf: OK, 1 page (lang=en)" in report
    assert "Selected Projects included: no" in report
    assert "Experience order: Acme Corp -> Globex Pty Ltd" in report
    assert "analysis.md gaps not covered: X" in report


def test_build_report_marks_failed_job():
    jobs = [RenderJob("t.html", "missing.json", "out.pdf")]
    results = [RenderResult(pdf="out.pdf", pages=0, ok=False, log="boom", html=None)]
    report = build_report(jobs, results)
    assert "out.pdf: FAILED" in report


def test_build_report_empty_without_any_job():
    assert build_report([], []) == ""
