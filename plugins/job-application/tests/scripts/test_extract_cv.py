import subprocess
import sys
from pathlib import Path

import docx
import pymupdf
import pytest

from jobkit.extract_cv import extract_text


def test_reads_md_verbatim(tmp_path):
    p = tmp_path / "a.md"
    p.write_text("# Sample Dev\nC++ engineer", encoding="utf-8")
    assert "C++ engineer" in extract_text(str(p))


def test_reads_tex_verbatim(tmp_path):
    p = tmp_path / "a.tex"
    p.write_text(r"\section{Experience} Globex", encoding="utf-8")
    assert "Globex" in extract_text(str(p))


def test_reads_txt_verbatim(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("Plain text CV content", encoding="utf-8")
    assert "Plain text CV content" in extract_text(str(p))


def test_unsupported_extension_raises(tmp_path):
    p = tmp_path / "a.rtf"
    p.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="Unsupported"):
        extract_text(str(p))


def test_extracts_pdf_text(tmp_path):
    p = tmp_path / "a.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Extracted PDF marker text")
    doc.save(str(p))
    doc.close()
    assert "Extracted PDF marker text" in extract_text(str(p))


def test_extracts_docx_text(tmp_path):
    p = tmp_path / "a.docx"
    d = docx.Document()
    d.add_paragraph("Extracted docx marker text")
    d.save(str(p))
    assert "Extracted docx marker text" in extract_text(str(p))


def test_cli_missing_path_exits_2():
    result = subprocess.run(
        [sys.executable, "-m", "jobkit", "extract-cv"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2


def test_cli_unsupported_extension_exits_2(tmp_path):
    p = tmp_path / "a.rtf"
    p.write_text("x", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "jobkit", "extract-cv", str(p)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "Unsupported" in result.stderr
