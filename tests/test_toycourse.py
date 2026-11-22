"""Tests for the synthetic WM2001 toy course generator (tests/fixtures/make_toycourse.py)."""
import importlib.util
import json
import re
from pathlib import Path

import pymupdf
import pytest

import validate_course_md as v

GEN = Path(__file__).resolve().parent / "fixtures" / "make_toycourse.py"
_spec = importlib.util.spec_from_file_location("make_toycourse", GEN)
tc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tc)

PDFS = ["book.pdf", "slides/L01.pdf", "slides/L02.pdf", "slides/L03.pdf",
        "assignments/A1.pdf", "assignments/A2.pdf", "papers/2023.pdf", "papers/2024.pdf"]
TEXT_FILES = ["course.expected.md", "papers/marks.json"]


@pytest.fixture(scope="module")
def out(tmp_path_factory):
    d = tmp_path_factory.mktemp("toycourse")
    assert tc.main([str(d)]) == 0
    return d


def norm(s):
    return re.sub(r"\s+", " ", s)


def pdf_texts(path):
    with pymupdf.open(path) as doc:
        return [p.get_text() for p in doc]


def footer(page):
    r = page.rect
    return page.get_text(clip=pymupdf.Rect(0, r.height - 50, r.width, r.height)).strip()


def test_files_exist(out):
    for f in PDFS + TEXT_FILES:
        assert (out / f).is_file(), f


def test_pdfs_have_text(out):
    for f in PDFS:
        texts = pdf_texts(out / f)
        assert texts and all(t.strip() for t in texts), f


def test_slide_decks_are_landscape_with_4_to_6_slides(out):
    for code in ("L01", "L02", "L03"):
        with pymupdf.open(out / "slides" / f"{code}.pdf") as doc:
            assert 4 <= doc.page_count <= 6
            assert all(p.rect.width > p.rect.height for p in doc)
            assert "Prof. A. Example" in doc[0].get_text()


def test_book_offset_is_6(out):
    with pymupdf.open(out / "book.pdf") as doc:
        assert 28 <= doc.page_count <= 32
        assert [footer(doc[i]) for i in range(6)] == [""] * 6
        assert footer(doc[6]) == "1"          # printed page 1 is PDF page 7
        for i in range(6, doc.page_count):
            assert footer(doc[i]) == str(i + 1 - 6)


def test_chapter_pages_match_course_md(out):
    c = v.load_valid(out / "course.expected.md")
    off = c["book"]["page_offset"]
    texts = pdf_texts(out / "book.pdf")
    for ch in c["chapters"]:
        first, last = ch["pages"]
        assert texts[first + off - 1].startswith(f"Chapter {ch['id']}  {ch['title']}")
        assert "Exercises" in texts[last + off - 1]
    assert "Fig. 1.1" in "".join(texts) and "Standard values" in "".join(texts)


def test_paper_marks_sum_to_50(out):
    marks = json.loads((out / "papers" / "marks.json").read_text())
    assert set(marks) == {"2023", "2024"}
    for year, qs in marks.items():
        assert sum(q["marks"] for q in qs.values()) == 50
        text = "".join(pdf_texts(out / "papers" / f"{year}.pdf"))
        printed = [int(m) for m in re.findall(r"\[(\d+) marks?\]", text)]
        assert sum(printed) == 50
        assert printed == [q["marks"] for _, q in sorted(qs.items())]
        assert "Use: tau = 16T/(pi d^3)" in text      # papers print some formulas


def test_chapter_distribution_differs_and_one_chapter_in_one_paper(out):
    marks = json.loads((out / "papers" / "marks.json").read_text())
    per = {y: {} for y in marks}
    for y, qs in marks.items():
        for q in qs.values():
            per[y][q["chapter"]] = per[y].get(q["chapter"], 0) + q["marks"]
    assert per["2023"] == {"1": 18, "2": 16, "3": 14, "4": 2}
    assert per["2024"] == {"2": 14, "3": 18, "4": 18}


def test_course_expected_validates(out):
    p = out / "course.expected.md"
    assert v.validate(p) == []
    c = v.load_valid(p)
    assert c["front"]["paper_total"] == 50 and c["book"]["page_offset"] == 6
    assert [ch["self_rating"] for ch in c["chapters"]] == [2, 4, 3, 1]
    marks = json.loads((out / "papers" / "marks.json").read_text())
    for ch in c["chapters"]:
        for e in ch["past_papers"]:
            q = marks[e["paper"]][e["question"]]
            assert q["chapter"] == ch["id"] and q["marks"] == e["marks"]
    n = sum(len(ch["past_papers"]) for ch in c["chapters"])
    assert n == sum(len(qs) for qs in marks.values())


def test_planted_errors_in_book(out):
    texts = [norm(t) for t in pdf_texts(out / "book.pdf")]
    for name, e in tc.PLANTED.items():
        page = e["printed_page"] + tc.FRONT_PAGES
        assert e["text"] in texts[page - 1], name
        assert sum(e["text"] in t for t in texts) == 1, name
    full = " ".join(texts)
    assert "Precision spindles are limited to 0.25 deg/m" in full    # truth is derivable
    assert "E = 0.5 x 146 x 2.0^2 = 292 J" in full


def test_slides_contradiction_and_emphasis(out):
    l02 = norm(" ".join(pdf_texts(out / "slides" / "L02.pdf")))
    assert "use stress area A_t, not nominal area" in l02
    assert "C = 421.5 / (421.5 + 1400) = 0.231" in l02
    book = norm(" ".join(pdf_texts(out / "book.pdf")))
    assert "= 0.288" in book and "0.231" not in book
    assert "IMPORTANT for exam" in " ".join(pdf_texts(out / "slides" / "L03.pdf"))


def test_generator_is_deterministic(out, tmp_path):
    assert tc.main([str(tmp_path)]) == 0
    for f in PDFS:
        assert pdf_texts(out / f) == pdf_texts(tmp_path / f), f
    for f in TEXT_FILES:
        assert (out / f).read_bytes() == (tmp_path / f).read_bytes(), f
