import check_ascii
import check_overfull
import pdf_pages
import pytest


def test_ascii_clean(tmp_path):
    f = tmp_path / "a.tex"; f.write_text("plain $\\mu$ -- ok\n")
    assert check_ascii.scan(f) == []
    assert check_ascii.main([str(f)]) == 0


def test_ascii_reports_position_and_replacement(tmp_path):
    f = tmp_path / "a.tex"; f.write_text("ok\nstress σ = 5 – 10°C\n")
    hits = check_ascii.scan(f)
    assert [(h["line"], h["col"]) for h in hits] == [(2, 8), (2, 14), (2, 18)]
    assert hits[0]["replacement"] == "$\\sigma$"
    assert hits[1]["replacement"] == "--"
    assert hits[2]["replacement"] == "\\degree{} or $^\\circ$"
    assert check_ascii.main([str(f)]) == 1


def test_ascii_unknown_char_still_reported(tmp_path):
    f = tmp_path / "a.tex"; f.write_text("x ☃\n")
    (h,) = check_ascii.scan(f)
    assert h["char"] == "☃" and h["replacement"]


LOG = """(./x.tex
Overfull \\hbox (12.5pt too wide) in paragraph at lines 10--12
[]\\T1/lmr/m/n/10 something
Overfull \\hbox (0.3pt too wide) in paragraph at lines 20--20
Overfull \\vbox (3.0pt too high) has occurred while \\output is active
Underfull \\hbox (badness 10000) in paragraph at lines 5--6
"""


def test_overfull_threshold(tmp_path):
    f = tmp_path / "x.log"; f.write_text(LOG)
    hits = check_overfull.scan(f, threshold=1.0)
    assert [(h["kind"], h["amount"], h["lines"]) for h in hits] == [
        ("hbox", 12.5, "10--12"), ("vbox", 3.0, None)]
    assert check_overfull.main([str(f)]) == 1
    assert check_overfull.main([str(f), "--threshold", "20"]) == 0


def test_pdf_pages_roundtrip():
    assert pdf_pages.to_pdf(141, 24) == 165
    assert pdf_pages.to_printed(165, 24) == 141
    assert pdf_pages.main(["to-pdf", "141", "--offset", "24"]) == 0
    with pytest.raises(ValueError):
        pdf_pages.to_pdf(0, 24)
    with pytest.raises(ValueError):
        pdf_pages.to_printed(3, 6)      # front matter has no printed number
