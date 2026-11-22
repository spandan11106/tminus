import shutil

import pymupdf
import pytest

import pdf_text as pt

HAS_TESS = bool(shutil.which("tesseract"))


@pytest.fixture
def pdfs(tmp_path):
    # page 1: real text; page 2: the same kind of text rasterised (image-only)
    src = pymupdf.open()
    pg = src.new_page(width=400, height=200)
    pg.insert_text((30, 100), "Synchronous reactance test", fontsize=22)
    pix = pg.get_pixmap(dpi=200)
    doc = pymupdf.open()
    doc.new_page(width=400, height=200).insert_text(
        (30, 60), "Open circuit test\ngives the core loss and the magnetising branch\nof the equivalent circuit.", fontsize=12)
    img = doc.new_page(width=400, height=200)
    img.insert_image(img.rect, pixmap=pix)
    p = tmp_path / "mixed.pdf"; doc.save(p)
    return p


def test_scan_reports_image_only_pages(pdfs):
    r = pt.scan(pdfs)
    assert r["pages"] == 2 and r["image_only_pages"] == [2]
    assert r["verdict"] == "partly scanned"


def test_text_without_ocr(pdfs):
    out = pt.pages_text(pdfs, [1, 2], ocr=False)
    assert "Open circuit test" in out[1] and out[2].strip() == ""


@pytest.mark.skipif(not HAS_TESS, reason="tesseract not installed")
def test_text_with_ocr(pdfs):
    out = pt.pages_text(pdfs, [2], ocr=True)
    assert "synchronous" in out[2].lower()


def test_cli(pdfs, capsys):
    assert pt.main([str(pdfs), "--scan"]) == 0
    assert "image-only pages: 2" in capsys.readouterr().out
    assert pt.main([str(pdfs), "--pages", "1"]) == 0
    assert "Open circuit" in capsys.readouterr().out
