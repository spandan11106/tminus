#!/usr/bin/env python3
"""Page text with OCR fallback, and a scanned-PDF check.

  pdf_text.py FILE.pdf --scan                       -> pages, image-only pages, verdict
  pdf_text.py FILE.pdf --pages 12-14 [--no-ocr]     -> text of PDF pages (1-based), OCR for image-only pages
  pdf_text.py FILE.pdf --printed 141 --offset 24    -> text of printed page 141

OCR uses PyMuPDF with tesseract (optional; /tminus:doctor reports it). A page counts as image-only when it
has fewer than MIN_CHARS extractable characters.
"""
from __future__ import annotations

import shutil
import sys

try:
    import pymupdf
except ImportError:
    pymupdf = None

MIN_CHARS = 50


def _open(path):
    if pymupdf is None:
        raise RuntimeError("PyMuPDF is needed for pdf_text.py (or use pdftotext directly)")
    return pymupdf.open(path)


def scan(path) -> dict:
    doc = _open(path)
    img = [i + 1 for i, p in enumerate(doc) if len(p.get_text().strip()) < MIN_CHARS]
    n = doc.page_count
    verdict = "text" if not img else ("image-only, needs OCR" if len(img) >= 0.8 * n else "partly scanned")
    return {"pages": n, "image_only_pages": img, "verdict": verdict}


def pages_text(path, pages, ocr=True, lang="eng") -> dict:
    doc = _open(path)
    can_ocr = ocr and bool(shutil.which("tesseract"))
    out = {}
    for n in pages:
        p = doc[n - 1]
        t = p.get_text()
        if len(t.strip()) < MIN_CHARS and can_ocr:
            t = p.get_textpage_ocr(language=lang, dpi=300, full=True).extractText()
        out[n] = t
    return out


def _range(s: str) -> list[int]:
    out = []
    for part in s.split(","):
        a, _, b = part.partition("-")
        out += list(range(int(a), int(b or a) + 1))
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    opt = lambda k: argv[argv.index(k) + 1] if k in argv else None
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        if "--scan" in argv:
            r = scan(argv[0])
            img = r["image_only_pages"]
            print(f"{argv[0]}: {r['pages']} pages, {r['verdict']}; image-only pages: "
                  f"{', '.join(map(str, img[:30])) + (' ...' if len(img) > 30 else '') if img else 'none'}")
            if img and not shutil.which("tesseract"):
                print("OCR not available: install tesseract (see /tminus:doctor)")
            return 0
        if opt("--printed"):
            pages = [int(opt("--printed")) + int(opt("--offset") or 0)]
        else:
            pages = _range(opt("--pages") or "1")
        for n, t in pages_text(argv[0], pages, ocr="--no-ocr" not in argv).items():
            print(f"===== PDF page {n} =====\n{t}")
    except (RuntimeError, ValueError, IndexError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
