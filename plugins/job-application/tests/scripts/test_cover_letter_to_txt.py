import json
from pathlib import Path

import pytest

from jobkit.cover_txt import cover_letter_to_text


def _write(tmp_path, name, data):
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_english_full_schema(tmp_path):
    data = {
        "name": "Sample Dev",
        "contact": ["x@example.com", "github.com/s"],
        "date": "September 1, 2026",
        "recipient": ["Hiring Manager", "Acme Corp"],
        "subject": "Application for the Position of X",
        "salutation": "Dear Hiring Manager,",
        "paragraphs": ["Para one.", "Para two."],
        "closing": "Sincerely,",
        "signature": "Sample Dev",
    }
    j = _write(tmp_path, "cl.json", data)
    out = tmp_path / "cl.txt"
    text = cover_letter_to_text(str(j), str(out))
    assert out.is_file()
    assert text.split("\n")[0] == "Subject: Application for the Position of X"
    assert "Date: September 1, 2026" in text
    assert "Dear Hiring Manager," in text
    assert "Para one.\n\nPara two." in text
    assert text.rstrip().endswith("Sample Dev")
    assert text.endswith("\n") and not text.endswith("\n\n")


def test_chinese_letter_localized_labels(tmp_path):
    data = {
        "lang": "zh",
        "name": "王开发",
        "contact": ["x@example.com"],
        "date": "2026年9月1日",
        "recipient": ["招聘经理"],
        "subject": "应聘软件工程师职位",
        "salutation": "尊敬的招聘经理：",
        "paragraphs": ["第一段。"],
        "closing": "此致",
        "signature": "王开发",
    }
    j = _write(tmp_path, "cl-zh.json", data)
    text = cover_letter_to_text(str(j), str(tmp_path / "cl-zh.txt"))
    assert text.split("\n")[0] == "主题：应聘软件工程师职位"
    assert "日期：2026年9月1日" in text


def test_contact_objects_flattened(tmp_path):
    data = {
        "name": "Obj Dev",
        "contact": [{"text": "a@b.com", "href": "mailto:a@b.com"}, "github.com/x"],
        "subject": "S",
        "paragraphs": ["p"],
    }
    j = _write(tmp_path, "cl-contact.json", data)
    text = cover_letter_to_text(str(j), str(tmp_path / "cl-contact.txt"))
    assert "a@b.com  |  github.com/x" in text


def test_minimal_fixture_no_triple_newline(tmp_path):
    data = {"name": "X", "subject": "Y", "paragraphs": ["p"]}
    j = _write(tmp_path, "cl-min.json", data)
    text = cover_letter_to_text(str(j), str(tmp_path / "cl-min.txt"))
    assert text.split("\n")[0] == "Subject: Y"
    assert "\n\n\n" not in text


def test_non_object_null_raises(tmp_path):
    j = tmp_path / "cl-null.json"
    j.write_text("null", encoding="utf-8")
    with pytest.raises(ValueError):
        cover_letter_to_text(str(j), str(tmp_path / "cl-null.txt"))


def test_non_object_string_raises(tmp_path):
    j = tmp_path / "cl-str.json"
    j.write_text('"hello"', encoding="utf-8")
    with pytest.raises(ValueError):
        cover_letter_to_text(str(j), str(tmp_path / "cl-str.txt"))


def test_default_out_path_beside_data_path(tmp_path):
    data = {"name": "X", "subject": "Y", "paragraphs": ["p"]}
    j = _write(tmp_path, "cl.json", data)
    cover_letter_to_text(str(j))
    assert (tmp_path / "cover_letter.txt").is_file()
