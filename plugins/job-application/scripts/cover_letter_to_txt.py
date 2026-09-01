"""Convert cover_letter.data.json into an email-ready plain-text cover letter.

The "Subject:" (or "主题：") line is hoisted to the first line so it can be
copied straight into an email's subject field.

CLI usage: `uv run --project ${CLAUDE_PLUGIN_ROOT} ${CLAUDE_PLUGIN_ROOT}/scripts/cover_letter_to_txt.py --data-path cover_letter.data.json [--out-path out.txt]`
"""
import argparse
import json
import re
import sys
from pathlib import Path


def _contact_text(entry) -> str:
    return entry if isinstance(entry, str) else entry.get("text", "")


def cover_letter_to_text(data_path: str, out_path: str | None = None) -> str:
    data = json.loads(Path(data_path).read_text(encoding="utf-8"))
    # Reject valid-but-non-object JSON (null / "x" / 123 / []) — mirrors the
    # `if (!data || typeof data !== "object")` guard in cover_letter.html.
    if not isinstance(data, dict):
        raise ValueError("cover_letter.data.json is not a JSON object")
    if out_path is None:
        out_path = str(Path(data_path).resolve().parent / "cover_letter.txt")
    is_zh = data.get("lang") == "zh"

    lines: list[str] = []

    lines.append(
        f"主题：{data.get('subject', '')}" if is_zh else f"Subject: {data.get('subject', '')}"
    )
    lines.append("")

    lines.append(str(data.get("name", "")))
    contact = data.get("contact")
    if contact:
        lines.append("  |  ".join(_contact_text(c) for c in contact))
    lines.append("")

    if data.get("date"):
        lines.append(f"日期：{data['date']}" if is_zh else f"Date: {data['date']}")
        lines.append("")

    recipient = data.get("recipient")
    if recipient:
        lines.extend(str(r) for r in recipient)
        lines.append("")

    if data.get("salutation"):
        lines.append(str(data["salutation"]))
        lines.append("")

    paragraphs = data.get("paragraphs")
    if paragraphs:
        for i, para in enumerate(paragraphs):
            lines.append(str(para))
            if i < len(paragraphs) - 1:
                lines.append("")
        lines.append("")

    if data.get("closing"):
        lines.append(str(data["closing"]))
        lines.append("")
    if data.get("signature"):
        lines.append(str(data["signature"]))

    text = "\n".join(lines)
    text = re.sub(r"[ \t]+(\n)", r"\1", text)
    text = text.rstrip() + "\n"

    Path(out_path).write_text(text, encoding="utf-8", newline="\n")
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", required=True)
    parser.add_argument("--out-path")
    args = parser.parse_args()
    try:
        cover_letter_to_text(args.data_path, args.out_path)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    out = args.out_path or str(Path(args.data_path).resolve().parent / "cover_letter.txt")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
