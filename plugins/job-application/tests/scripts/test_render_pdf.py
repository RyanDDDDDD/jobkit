import inspect
import subprocess
import sys
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from extract_cv import extract_text  # noqa: E402
from render_pdf import render_pdf  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
TEMPLATE = REPO / "templates" / "resume.html"
COVER_TEMPLATE = REPO / "templates" / "cover_letter.html"

# Structural checks that do not launch Chromium.
_NO_CHROMIUM_TESTS = {
    "test_render_pdf_has_no_placeholder_param",
    "test_both_templates_use_the_shared_data_token",
}


@pytest.fixture(scope="session")
def chromium_available() -> bool:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            browser.close()
        return True
    except Exception:
        return False


@pytest.fixture(autouse=True)
def _skip_without_chromium(request, chromium_available):
    if request.node.name in _NO_CHROMIUM_TESTS:
        return
    if not chromium_available:
        pytest.skip("no Chromium available (run `uv run playwright install chromium`)")


def test_render_pdf_has_no_placeholder_param():
    assert "placeholder" not in inspect.signature(render_pdf).parameters


def test_both_templates_use_the_shared_data_token():
    for tpl in (TEMPLATE, COVER_TEMPLATE):
        text = tpl.read_text(encoding="utf-8")
        assert "{{DATA_JSON}}" in text
        assert "{{RESUME_JSON}}" not in text
        assert "{{COVER_LETTER_JSON}}" not in text


def test_cover_letter_renders_with_shared_token(tmp_path):
    data = tmp_path / "cl.json"
    data.write_text(
        '{"name":"Testy McTest","subject":"Application for the Position of X",'
        '"salutation":"Dear Hiring Manager,","paragraphs":["I am writing to apply."],'
        '"closing":"Sincerely,","signature":"Testy McTest"}',
        encoding="utf-8",
    )
    result = render_pdf(str(COVER_TEMPLATE), str(data), str(tmp_path / "cl.pdf"))
    assert result.ok, result.log
    text = extract_text(result.pdf)
    assert "Invalid cover letter JSON" not in text
    assert "Application for the Position of X" in text


def test_small_json_renders_one_page(tmp_path):
    data = tmp_path / "s.json"
    data.write_text(
        '{"name":"Testy McTest","contact":["x@example.com"],'
        '"sections":[{"title":"Skills","type":"skills","groups":'
        '[{"label":"Languages","value":"Python"}]}]}',
        encoding="utf-8",
    )
    result = render_pdf(str(TEMPLATE), str(data), str(tmp_path / "s.pdf"))
    assert result.ok
    assert result.pages == 1
    assert Path(result.pdf).is_file()


def test_large_json_renders_multiple_pages(tmp_path):
    roles = []
    for i in range(1, 6):
        bullets = ",".join(
            f'"Delivered a substantial body of work item {b} for role {i}, '
            f'spanning design, implementation, rollout and measurement across '
            f'several teams and quarters."'
            for b in range(1, 9)
        )
        roles.append(
            f'{{"primary":"Senior Engineer {i}","secondary":"Company {i}",'
            f'"dates":"20{9+i}-20{10+i}","stack":"TypeScript, Go, PostgreSQL, '
            f'Kubernetes","bullets":[{bullets}]}}'
        )
    big = (
        '{"name":"Big Resume","contact":["big@example.com","555-0100"],'
        '"intro":["A senior engineer with a long and detailed track record '
        'across many organisations."],'
        f'"sections":[{{"title":"Experience","type":"entries","items":[{",".join(roles)}]}}]}}'
    )
    data = tmp_path / "b.json"
    data.write_text(big, encoding="utf-8")
    result = render_pdf(str(TEMPLATE), str(data), str(tmp_path / "b.pdf"))
    assert result.ok
    assert result.pages >= 3


def test_malformed_json_still_renders_error_page(tmp_path):
    data = tmp_path / "bad.json"
    data.write_text("{ this is not json", encoding="utf-8")
    result = render_pdf(str(TEMPLATE), str(data), str(tmp_path / "bad.pdf"))
    assert result.ok
    text = extract_text(result.pdf)
    assert "Invalid resume JSON" in text


def test_data_with_closing_script_tag_does_not_break_page(tmp_path):
    data = tmp_path / "endtag.json"
    data.write_text(
        '{"name":"Testy McTest","contact":["x@example.com"],"sections":['
        '{"title":"Experience","type":"entries","items":[{"primary":"Engineer",'
        '"secondary":"Co","bullets":["Removed inline </script> tags from the '
        'checkout page"]}]}]}',
        encoding="utf-8",
    )
    result = render_pdf(str(TEMPLATE), str(data), str(tmp_path / "endtag.pdf"))
    assert result.ok
    assert result.pages >= 1
    text = extract_text(result.pdf)
    assert "checkout page" in text
    assert "Invalid resume JSON" not in text


def test_output_path_with_space_renders_ok(tmp_path):
    space_dir = tmp_path / "Jane Street"
    space_dir.mkdir()
    data = tmp_path / "s.json"
    data.write_text('{"name":"Testy McTest","contact":["x@example.com"]}', encoding="utf-8")
    result = render_pdf(str(TEMPLATE), str(data), str(space_dir / "resume.pdf"))
    assert result.ok
    assert result.pages == 1
    assert Path(result.pdf).is_file()


def test_keep_html_rewrites_font_urls_to_absolute(tmp_path):
    data = tmp_path / "s.json"
    data.write_text('{"name":"Testy McTest","contact":["x@example.com"]}', encoding="utf-8")
    result = render_pdf(str(TEMPLATE), str(data), str(tmp_path / "k.pdf"), keep_html=True)
    rendered = Path(result.html).read_text(encoding="utf-8")
    assert 'url("fonts/' not in rendered
    assert rendered.count('src: url("file://') == 2


def test_keep_html_lands_next_to_data_path(tmp_path):
    """The .rendered.html sits beside the data file, not the output PDF -- so
    `apply` can keep data in tmp/ while the PDF stays flat."""
    data_dir = tmp_path / "tmp"
    data_dir.mkdir()
    data = data_dir / "resume.data.json"
    data.write_text('{"name": "T", "sections": []}', encoding="utf-8")
    out_pdf = tmp_path / "resume.pdf"  # flat, a level up from the data file
    result = render_pdf(str(TEMPLATE), str(data), str(out_pdf), keep_html=True)
    assert result.ok, result.log
    assert result.html is not None
    html_path = Path(result.html)
    assert html_path.parent == data_dir
    assert html_path.name == "resume.rendered.html"
    assert html_path.is_file()
