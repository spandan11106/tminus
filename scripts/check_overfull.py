#!/usr/bin/env python3
"""Overfull gate: parse a LaTeX .log and report Overfull \\hbox / \\vbox above a threshold.

Usage: check_overfull.py FILE.log [--threshold PT]   (default 1.0 pt)
exit 0 none above threshold, 1 otherwise.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

PAT = re.compile(r"Overfull \\(hbox|vbox) \((\d+(?:\.\d+)?)pt too (?:wide|high)\)"
                 r"(?:.*?at lines? (\d+--\d+|\d+))?")


def scan(path, threshold: float = 1.0) -> list[dict]:
    hits = []
    for line in Path(path).read_text(encoding="latin-1").splitlines():
        m = PAT.search(line)
        if m and float(m.group(2)) > threshold:
            hits.append({"kind": m.group(1), "amount": float(m.group(2)), "lines": m.group(3)})
    return hits


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: check_overfull.py FILE.log [--threshold PT]", file=sys.stderr)
        return 2
    thr = float(argv[argv.index("--threshold") + 1]) if "--threshold" in argv else 1.0
    hits = scan(argv[0], thr)
    for h in hits:
        where = f"source lines {h['lines']}" if h["lines"] else "while shipping a page"
        print(f"Overfull \\{h['kind']} {h['amount']}pt ({where})")
    if hits:
        print(f"Overfull gate FAILED: {len(hits)} box(es) over {thr}pt")
        return 1
    print(f"Overfull gate OK (threshold {thr}pt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
