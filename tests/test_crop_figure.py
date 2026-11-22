import shutil

import pymupdf
import pytest

import crop_figure as cf


@pytest.fixture
def pdf(tmp_path):
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((72, 100), "Paragraph text above the figure that must not be in the crop.")
    page.draw_rect(pymupdf.Rect(150, 200, 450, 400), color=(0, 0, 0), width=2)
    page.draw_line((150, 200), (450, 400))
    page.insert_text((200, 425), "Fig. 2.1 A test figure")
    page.insert_text((72, 500), "Text below the caption, also excluded.")
    doc.new_page()
    p = tmp_path / "t.pdf"; doc.save(p)
    return p


def test_caption_bbox_contains_figure_not_text(pdf):
    bbox = cf.caption_bbox(pdf, 1, "Fig. 2.1")
    x0, y0, x1, y1 = bbox
    assert x0 <= 150 and x1 >= 450 and y0 <= 200 and y1 >= 425
    assert y0 > 105 and y1 < 490


def test_crop_by_caption_writes_png(pdf, tmp_path):
    out = tmp_path / "fig.png"
    info = cf.crop(pdf, 1, out, caption="Fig. 2.1", dpi=100)
    assert out.is_file() and out.stat().st_size > 0
    w, h = info["size_px"]
    assert 400 < w < 600 and 280 < h < 400


def test_crop_by_fraction_bbox(pdf, tmp_path):
    out = tmp_path / "half.png"
    info = cf.crop(pdf, 1, out, bbox=(0, 0, 0.5, 0.5), units="frac", dpi=72)
    assert info["size_px"] == (298, 421) or abs(info["size_px"][0] - 298) <= 1


def test_printed_page_via_offset(pdf, tmp_path):
    assert cf.resolve_page(page=None, printed=1, offset=0) == 1
    with pytest.raises(ValueError):
        cf.resolve_page(page=None, printed=None, offset=None)


def test_missing_caption_errors(pdf, tmp_path):
    with pytest.raises(LookupError):
        cf.crop(pdf, 1, tmp_path / "x.png", caption="Fig. 9.9")


@pytest.mark.skipif(not shutil.which("pdftoppm"), reason="pdftoppm not installed")
def test_pdftoppm_fallback(pdf, tmp_path, monkeypatch):
    monkeypatch.setattr(cf, "pymupdf", None)
    out = tmp_path / "fb.png"
    info = cf.crop(pdf, 1, out, bbox=(100, 150, 500, 450), units="pt", dpi=72)
    assert out.is_file() and info["renderer"] == "pdftoppm"
