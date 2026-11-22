#!/usr/bin/env bash
# build_doc.sh SOURCE [--out DIR] [--format pdf|md] [--threshold PT]
#
# The single place that picks an output engine:
#   format pdf: placeholder gate, ASCII gate, then latexmk -> tectonic -> pdflatex (x2),
#               then the overfull gate. Builds in a temp dir; only a fully built,
#               gate-passing PDF is moved into --out (default: the source's directory).
#   format md : placeholder gate, copy the .md into --out, and an .html too if pandoc exists.
# Format defaults from the extension (.tex -> pdf, .md -> md). Prints "engine: <name>".
# Exit: 0 ok, 1 a gate failed or the build failed, 3 pdf asked but no TeX engine (use md).
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"
PY="$(tminus_python)"

src="${1:?usage: build_doc.sh SOURCE [--out DIR] [--format pdf|md] [--threshold PT]}"; shift
out=""; fmt=""; thr="1.0"
while [ $# -gt 0 ]; do
  case "$1" in
    --out) out="$2"; shift 2;;
    --format) fmt="$2"; shift 2;;
    --threshold) thr="$2"; shift 2;;
    *) echo "build_doc: unknown option $1" >&2; exit 2;;
  esac
done
[ -f "$src" ] || { echo "build_doc: no such file: $src" >&2; exit 2; }
srcdir="$(cd "$(dirname "$src")" && pwd)"; base="$(basename "$src")"; stem="${base%.*}"
out="${out:-$srcdir}"; mkdir -p "$out"; out="$(cd "$out" && pwd)"
if [ -z "$fmt" ]; then case "$base" in *.tex) fmt=pdf;; *.md) fmt=md;; *) fmt=pdf;; esac; fi

# placeholder gate: no unfilled <<...>> from the templates may survive
if grep -nE '<<[A-Z_]+[^>]*>>' "$src" >/dev/null; then
  echo "Placeholder gate FAILED: unfilled template placeholders:"; grep -nE '<<[A-Z_]+[^>]*>>' "$src" | head -20
  exit 1
fi

if [ "$fmt" = md ]; then
  [ "$srcdir" = "$out" ] || cp "$src" "$out/$base"
  if command -v pandoc >/dev/null 2>&1; then
    tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
    pandoc "$src" -s --mathjax -o "$tmp/$stem.html" && mv "$tmp/$stem.html" "$out/$stem.html"
    echo "engine: markdown (+pandoc html)"
  else
    echo "engine: markdown"
  fi
  echo "output: $out/$base"; exit 0
fi

"$PY" -I "$TMINUS_SCRIPTS/check_ascii.py" "$src" || exit 1

engine="${TMINUS_ENGINE:-}"
if [ -z "$engine" ]; then
  if command -v latexmk >/dev/null 2>&1 && command -v pdflatex >/dev/null 2>&1; then engine=latexmk
  elif command -v tectonic >/dev/null 2>&1; then engine=tectonic
  elif command -v pdflatex >/dev/null 2>&1; then engine=pdflatex
  else
    echo "engine: none -- no TeX engine on PATH. Set 'format: md' in course.md or run /tminus:doctor." >&2
    exit 3
  fi
fi
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
# "." first, so a user file named like a template (pack.tex) is never shadowed by it
export TEXINPUTS=".:$TMINUS_ROOT/templates//:${TEXINPUTS:-}"
cd "$srcdir"
set +e
case "$engine" in
  latexmk)  latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir="$tmp" "$base" >"$tmp/build.out" 2>&1;;
  tectonic) tectonic -Z search-path="$TMINUS_ROOT/templates" --keep-logs -o "$tmp" "$base" >"$tmp/build.out" 2>&1;;
  pdflatex) pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$tmp" "$base" >"$tmp/build.out" 2>&1 &&
            pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$tmp" "$base" >>"$tmp/build.out" 2>&1;;
  *) echo "build_doc: unknown engine $engine" >&2; exit 2;;
esac
rc=$?
set -e
echo "engine: $engine"
if [ $rc -ne 0 ] || [ ! -s "$tmp/$stem.pdf" ]; then
  echo "BUILD FAILED ($engine). Last errors:"
  grep -nE '^!|Error' "$tmp/$stem.log" 2>/dev/null | head -15 || tail -20 "$tmp/build.out"
  exit 1
fi
if grep -q 'Label(s) may have changed\|There were undefined references' "$tmp/$stem.log"; then
  echo "WARNING: undefined references remain"
fi
if grep -q 'headheight is too small' "$tmp/$stem.log"; then
  echo "WARNING: header taller than \\headheight (long title); shorten \\tmsetcourse or \\tmsetdoc"
fi
"$PY" -I "$TMINUS_SCRIPTS/check_overfull.py" "$tmp/$stem.log" --threshold "$thr" || exit 1
mv "$tmp/$stem.pdf" "$out/$stem.pdf"
pages="$(grep -o 'Output written on .*(\([0-9]*\) page' "$tmp/$stem.log" 2>/dev/null | grep -o '([0-9]*' | tr -d '(' || true)"
echo "output: $out/$stem.pdf ($pages pages)"
