"""Compress a PDF in place using pikepdf, keeping the original untouched if
compression does not shrink it (or fails).

CLI: jobkit compress --pdf resume.pdf [--pdf cover_letter.pdf ...]
"""
import argparse
import sys
from pathlib import Path

import pikepdf


def compress_pdf(pdf_path: str) -> str:
    path = Path(pdf_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    orig_size = path.stat().st_size
    temp_path = path.parent / (path.stem + ".temp.pdf")
    temp_path.unlink(missing_ok=True)

    # Compress into a temp file; never touch the original until it succeeds.
    with pikepdf.open(path) as pdf:
        pdf.save(
            temp_path,
            compress_streams=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
        )

    new_size = temp_path.stat().st_size
    if new_size >= orig_size:
        temp_path.unlink(missing_ok=True)
        return (
            f"compress_pdf: compressed output ({new_size} bytes) is not smaller "
            f"than the original ({orig_size} bytes); keeping the original."
        )

    temp_path.replace(path)
    return f"Successfully compressed {path} ({orig_size} -> {new_size} bytes)"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-path", action="append", required=True)
    args = parser.parse_args()
    failed = False
    for path in args.pdf_path:
        try:
            print(compress_pdf(path))
        except Exception as exc:
            failed = True
            print(str(exc), file=sys.stderr)
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
