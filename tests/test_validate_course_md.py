import shutil
from pathlib import Path

import pytest

import validate_course_md as v

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "course.template.md"


def make(tmp_path, text=None, with_book=True):
    text = TEMPLATE.read_text() if text is None else text
    p = tmp_path / "course.md"
    p.write_text(text)
    if with_book:
        (tmp_path / "book.pdf").write_bytes(b"%PDF-1.4\n")
    return p


def test_template_is_valid(tmp_path):
    errs = v.validate(make(tmp_path))
    assert errs == []


def test_missing_book(tmp_path):
    errs = v.validate(make(tmp_path, with_book=False))
    assert any("book" in e.lower() and "not found" in e for e in errs)


def test_bad_offset(tmp_path):
    t = TEMPLATE.read_text().replace("page_offset: 0", "page_offset: twelve")
    errs = v.validate(make(tmp_path, t))
    assert any("page_offset" in e for e in errs)


def test_empty_chapter_table(tmp_path):
    t = TEMPLATE.read_text().replace(
        "| 1 | First chapter | 1-20 | L01, L02 | A1 | 2024 Q2 (10) | 3 |\n", "")
    errs = v.validate(make(tmp_path, t))
    assert any("no chapter rows" in e for e in errs)


def test_bad_rating(tmp_path):
    t = TEMPLATE.read_text().replace("2024 Q2 (10) | 3 |", "2024 Q2 (10) | 7 |")
    errs = v.validate(make(tmp_path, t))
    assert any("self-rating" in e for e in errs)


def test_missing_section(tmp_path):
    t = TEMPLATE.read_text().replace("## Verified corrections log", "## Something else")
    errs = v.validate(make(tmp_path, t))
    assert any("Verified corrections log" in e for e in errs)


def test_missing_front_matter_field(tmp_path):
    t = TEMPLATE.read_text().replace("hours_per_day: 6", "")
    errs = v.validate(make(tmp_path, t))
    assert any("hours_per_day" in e for e in errs)


def test_bad_enum_and_date(tmp_path):
    t = (TEMPLATE.read_text().replace("format: pdf", "format: docx")
         .replace("exam_datetime: 2026-01-01T09:00", "exam_datetime: next tuesday"))
    errs = v.validate(make(tmp_path, t))
    assert any("format" in e for e in errs)
    assert any("exam_datetime" in e for e in errs)


def test_load_parses_chapters_and_past_papers(tmp_path):
    c = v.load_valid(make(tmp_path))
    assert c["book"]["page_offset"] == 0
    ch = c["chapters"][0]
    assert ch["id"] == "1" and ch["self_rating"] == 3
    assert ch["past_papers"] == [{"paper": "2024", "question": "Q2", "marks": 10.0}]
    assert ch["pages"] == (1, 20)


def test_cli_exit_codes(tmp_path):
    good = make(tmp_path)
    assert v.main([str(good)]) == 0
    bad = tmp_path / "bad"; bad.mkdir()
    p = make(bad, with_book=False)
    assert v.main([str(p)]) == 1
