#!/usr/bin/env python3
"""Render a PDF page and crop a figure to PNG.

  crop_figure.py PDF (--page N | --printed N --offset K) --out FILE.png
                 (--caption "Fig. 5.3" | --bbox x0,y0,x1,y1 [--units pt|frac]) [--dpi 200]

--caption finds the caption text on the page and crops from the text block above it down to the
caption (needs PyMuPDF). --bbox crops a box in PDF points (origin top-left) or page fractions.
Renderer: PyMuPDF, else pdftoppm (bbox only).
After cropping, VIEW the PNG before reading any value from it; mark chart reads as approx.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

try:
    import pymupdf
except ImportError:          # optional: pdftoppm fallback
    pymupdf = None

MAX_BYTES = 600_000


def resolve_page(page=None, printed=None, offset=None) -> int:
    if page:
        return int(page)
    if printed is not None and offset is not None:
        return int(printed) + int(offset)
    raise ValueError("give --page N (PDF page) or --printed N with --offset K")


def caption_bbox(pdf, page_no: int, caption: str, margin: float = 6.0):
    if pymupdf is None:
        raise RuntimeError("--caption needs PyMuPDF; use --bbox with pdftoppm")
    doc = pymupdf.open(pdf)
    page = doc[page_no - 1]
    blocks = [b for b in page.get_text("blocks") if b[6] == 0]
    norm = lambda s: " ".join(s.split()).lower()
    cap = next((b for b in blocks if norm(b[4]).startswith(norm(caption))), None)
    if cap is None:
        raise LookupError(f"caption '{caption}' not found on PDF page {page_no}")
    above = [b for b in blocks if b[3] <= cap[1] + 1 and b is not cap]
    top = max((b[3] for b in above), default=page.rect.y0)
    # figure extent: drawings and images between that block and the caption
    rects = [d["rect"] for d in page.get_drawings()]
    rects += [pymupdf.Rect(i["bbox"]) for i in page.get_image_info()]
    inside = [r for r in rects if r.y0 >= top - 1 and r.y1 <= cap[1] + 1]
    xs = [(cap[0], cap[2])] + [(r.x0, r.x1) for r in inside]
    if inside:                      # tight top edge when the figure is vector art or an image
        top = max(top, min(r.y0 for r in inside) - margin)
    x0 = max(page.rect.x0, min(a for a, _ in xs) - margin)
    x1 = min(page.rect.x1, max(b for _, b in xs) + margin)
    return (x0, max(page.rect.y0, top + 1), x1, min(page.rect.y1, cap[3] + margin))


def _page_size(pdf, page_no):
    if pymupdf is not None:
        r = pymupdf.open(pdf)[page_no - 1].rect
        return r.width, r.height
    out = subprocess.run(["pdfinfo", "-f", str(page_no), "-l", str(page_no), str(pdf)],
                         capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        if line.startswith(f"Page {page_no:>4} size:") or (line.startswith("Page") and "size:" in line):
            parts = line.split("size:")[1].split()
            return float(parts[0]), float(parts[2])
    raise RuntimeError("could not read page size")


def crop(pdf, page_no: int, out, caption=None, bbox=None, units="pt", dpi=200) -> dict:
    pdf, out = Path(pdf), Path(out)
    if caption:
        bbox = caption_bbox(pdf, page_no, caption)
        units = "pt"
    if bbox is None:
        raise ValueError("give --caption or --bbox")
    if units == "frac":
        w, h = _page_size(pdf, page_no)
        bbox = (bbox[0] * w, bbox[1] * h, bbox[2] * w, bbox[3] * h)
    out.parent.mkdir(parents=True, exist_ok=True)
    if pymupdf is not None:
        page = pymupdf.open(pdf)[page_no - 1]
        pix = page.get_pixmap(dpi=dpi, clip=pymupdf.Rect(*bbox))
        pix.save(out)
        size, renderer = (pix.width, pix.height), "pymupdf"
    else:
        if not shutil.which("pdftoppm"):
            raise RuntimeError("neither PyMuPDF nor pdftoppm is available (run /tminus:doctor)")
        s = dpi / 72
        x, y, W, H = (round(bbox[0] * s), round(bbox[1] * s), round((bbox[2] - bbox[0]) * s),
                      round((bbox[3] - bbox[1]) * s))
        stem = out.with_suffix("")
        subprocess.run(["pdftoppm", "-png", "-singlefile", "-r", str(dpi), "-f", str(page_no), "-l",
                        str(page_no), "-x", str(x), "-y", str(y), "-W", str(W), "-H", str(H),
                        str(pdf), str(stem)], check=True)
        size, renderer = (W, H), "pdftoppm"
    nbytes = out.stat().st_size
    return {"out": str(out), "page": page_no, "bbox_pt": tuple(round(v, 1) for v in bbox),
            "size_px": size, "bytes": nbytes, "renderer": renderer,
            "warning": f"larger than {MAX_BYTES // 1000} KB: lower --dpi" if nbytes > MAX_BYTES else ""}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    opt = lambda k: argv[argv.index(k) + 1] if k in argv else None
    if not argv or not opt("--out"):
        print(__doc__, file=sys.stderr)
        return 2
    try:
        page = resolve_page(opt("--page"), opt("--printed"), opt("--offset"))
        bbox = tuple(float(v) for v in opt("--bbox").split(",")) if opt("--bbox") else None
        info = crop(argv[0], page, opt("--out"), caption=opt("--caption"), bbox=bbox,
                    units=opt("--units") or "pt", dpi=int(opt("--dpi") or 200))
    except (ValueError, LookupError, RuntimeError, subprocess.CalledProcessError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    print(f"wrote {info['out']} ({info['size_px'][0]}x{info['size_px'][1]} px, {info['bytes'] // 1000} KB, "
          f"PDF page {info['page']}, bbox {info['bbox_pt']} pt, {info['renderer']})")
    if info["warning"]:
        print("WARNING: " + info["warning"])
    print("Now VIEW the image before using it or reading any value from it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
