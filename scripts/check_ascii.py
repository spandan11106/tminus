#!/usr/bin/env python3
"""ASCII gate for .tex files: report every non-ASCII character with a LaTeX-safe replacement.

Usage: check_ascii.py FILE.tex [FILE2.tex ...]   exit 0 clean, 1 if any non-ASCII found.
"""
from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

REPLACE = {
    "–": "--", "—": "---", "‘": "`", "’": "'", "“": "``", "”": "''",
    "…": "\\ldots{}", " ": "~", "°": "\\degree{} or $^\\circ$", "±": "$\\pm$",
    "×": "$\\times$", "÷": "$\\div$", "−": "$-$", "≤": "$\\le$", "≥": "$\\ge$",
    "≠": "$\\neq$", "≈": "$\\approx$", "∞": "$\\infty$", "→": "$\\to$",
    "⇒": "$\\Rightarrow$", "√": "$\\sqrt{}$", "²": "$^2$", "³": "$^3$",
    "µ": "$\\mu$", "′": "$'$", "•": "\\textbullet{}", "é": "\\'e",
    "α": "$\\alpha$", "β": "$\\beta$", "γ": "$\\gamma$", "δ": "$\\delta$",
    "ε": "$\\epsilon$", "η": "$\\eta$", "θ": "$\\theta$", "λ": "$\\lambda$",
    "μ": "$\\mu$", "ν": "$\\nu$", "π": "$\\pi$", "ρ": "$\\rho$",
    "σ": "$\\sigma$", "τ": "$\\tau$", "φ": "$\\phi$", "ω": "$\\omega$",
    "Δ": "$\\Delta$", "Σ": "$\\Sigma$", "Ω": "$\\Omega$", "Φ": "$\\Phi$",
}


def scan(path) -> list[dict]:
    hits = []
    for ln, line in enumerate(Path(path).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for col, ch in enumerate(line, 1):
            if ord(ch) > 127:
                name = unicodedata.name(ch, f"U+{ord(ch):04X}")
                hits.append({"file": str(path), "line": ln, "col": col, "char": ch, "name": name,
                             "replacement": REPLACE.get(ch, f"remove or replace (no mapping for {name})")})
    return hits


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: check_ascii.py FILE.tex ...", file=sys.stderr)
        return 2
    hits = [h for f in argv for h in scan(f)]
    for h in hits:
        print(f"{h['file']}:{h['line']}:{h['col']}: non-ASCII {h['char']!r} ({h['name']}) "
              f"-> use {h['replacement']}")
    if hits:
        print(f"ASCII gate FAILED: {len(hits)} character(s)")
        return 1
    print("ASCII gate OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
