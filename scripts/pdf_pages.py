#!/usr/bin/env python3
"""Printed-page <-> PDF-page conversion through course.md's page offset.

pdf_page = printed_page + offset.
CLI: pdf_pages.py to-pdf N --offset K | to-printed N --offset K | to-pdf N --course course.md
"""
from __future__ import annotations

import sys
from pathlib import Path


def to_pdf(printed: int, offset: int) -> int:
    if printed < 1:
        raise ValueError(f"printed page must be >= 1 (got {printed})")
    return printed + offset


def to_printed(pdf: int, offset: int) -> int:
    p = pdf - offset
    if p < 1:
        raise ValueError(f"PDF page {pdf} is front matter (offset {offset}); it has no printed number")
    return p


def _offset(argv) -> int:
    if "--offset" in argv:
        return int(argv[argv.index("--offset") + 1])
    if "--course" in argv:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from validate_course_md import load_valid
        return load_valid(argv[argv.index("--course") + 1])["book"]["page_offset"]
    raise SystemExit("need --offset K or --course course.md")


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) < 2 or argv[0] not in ("to-pdf", "to-printed"):
        print(__doc__, file=sys.stderr)
        return 2
    n, off = int(argv[1]), _offset(argv)
    print(to_pdf(n, off) if argv[0] == "to-pdf" else to_printed(n, off))
    return 0


if __name__ == "__main__":
    sys.exit(main())
