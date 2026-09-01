import subprocess
import sys
from pathlib import Path

import fitz
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from compress_pdf import compress_pdf  # noqa: E402

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "compress_pdf.py"
PROJECT = SCRIPT.parents[1]


def _make_uncompressed_pdf(path: Path, repeats: int = 400) -> None:
    doc = fitz.open()
    page = doc.new_page()
    text = "The quick brown fox jumps over the lazy dog. " * repeats
    # Wrap into a text box so PyMuPDF doesn't error on overflowing a single insert_text call.
    page.insert_textbox(page.rect, text, fontsize=6)
    doc.save(str(path), deflate=False)
    doc.close()


def test_compress_shrinks_a_larger_pdf(tmp_path):
    pdf = tmp_path / "big.pdf"
    _make_uncompressed_pdf(pdf)
    orig_size = pdf.stat().st_size

    message = compress_pdf(str(pdf))

    assert "Successfully compressed" in message
    assert pdf.stat().st_size < orig_size


def test_compress_keeps_original_when_not_smaller(tmp_path):
    pdf = tmp_path / "small.pdf"
    _make_uncompressed_pdf(pdf, repeats=1)
    # First pass compresses it about as far as pikepdf can.
    compress_pdf(str(pdf))
    before = pdf.read_bytes()

    # A second pass on an already-compressed file should not shrink it further.
    message = compress_pdf(str(pdf))

    assert "not smaller than the original" in message
    assert pdf.read_bytes() == before


def test_missing_file_raises(tmp_path):
    missing = tmp_path / "nope.pdf"
    with pytest.raises(FileNotFoundError, match="File not found"):
        compress_pdf(str(missing))


def test_cli_reports_failure_for_missing_file(tmp_path):
    missing = tmp_path / "nope.pdf"
    result = subprocess.run(
        ["uv", "run", "--project", str(PROJECT), str(SCRIPT), "--pdf-path", str(missing)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "File not found" in result.stderr
