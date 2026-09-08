"""Extract plain text from a CV or PDF file.

Handles .md/.tex/.txt (verbatim read), .pdf (PyMuPDF), and .docx (python-docx).
Reused both for ingesting past CVs and for verifying rendered resume/cover-letter
PDFs (`apply` / `reference/render-contract.md` silent-failure guard).

CLI: jobkit extract-cv <path>
prints the extracted text to stdout.
"""
import sys
from pathlib import Path

import docx
import fitz  # PyMuPDF's import name; the distributed package is "pymupdf"


def extract_text(path: str) -> str:
    p = Path(path).resolve()
    ext = p.suffix.lower()
    if ext in (".md", ".tex", ".txt"):
        return p.read_text(encoding="utf-8")
    if ext == ".pdf":
        doc = fitz.open(p)
        try:
            return "\n".join(page.get_text() for page in doc)
        finally:
            doc.close()
    if ext == ".docx":
        d = docx.Document(str(p))
        return "\n".join(paragraph.text for paragraph in d.paragraphs)
    raise ValueError(f"Unsupported file type: {ext}")


def main() -> None:
    if len(sys.argv) != 2:
        print("extract_cv.py: exactly one <path> argument is required", file=sys.stderr)
        sys.exit(2)
    try:
        print(extract_text(sys.argv[1]), end="")
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
