#!/usr/bin/env bash
# selftest.sh: unit tests, preflight simulation, template builds and gates, plugin validation.
# Usage: scripts/selftest.sh [--no-tex]   (--no-tex hides TeX from PATH to test Markdown mode)
# Exit non-zero on any failure. PDF gates report PENDING (not PASSED) when no TeX engine exists.
set -uo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"
cd "$TMINUS_ROOT"
PY="${TMINUS_TEST_PYTHON:-}"
if [ -z "$PY" ]; then
  if [ -x .venv/bin/python ]; then PY=.venv/bin/python; else PY="$(tminus_python)"; fi
fi
fail=0; step() { printf '\n== %s\n' "$*"; }

step "python deps"
"$PY" -c "import yaml, pytest" || { echo "need PyYAML and pytest: pip install -r requirements.txt"; exit 1; }

if [ "${1:-}" = "--no-tex" ]; then
  step "hiding TeX from PATH (Markdown-mode run)"
  shim="$(mktemp -d)"; trap 'rm -rf "$shim"' EXIT
  for t in bash sh env python3 grep sed cp mv rm mkdir mktemp dirname basename cat tr head tail awk git pdftotext pdftoppm pdfinfo claude; do
    p="$(command -v "$t" 2>/dev/null)" && ln -sf "$p" "$shim/$t"
  done
  export PATH="$shim"
fi

step "unit tests"
"$PY" -m pytest -q tests || fail=1

step "preflight on this machine"
"$PY" -I scripts/preflight.py; rc=$?
case $rc in 0) echo "preflight: all good";; 2) echo "preflight: usable (optional/PDF items missing)";;
  *) echo "preflight: REQUIRED item missing"; fail=1;; esac

step "PDF gates"
if command -v latexmk >/dev/null 2>&1 || command -v tectonic >/dev/null 2>&1 || command -v pdflatex >/dev/null 2>&1; then
  tmp="$(mktemp -d)"
  "$PY" - "$tmp" <<'PYEOF'
import re, sys, pathlib
for n in ("pack.tex", "cram.tex"):
    t = re.sub(r"<<[A-Z_]+[^>]*>>", "x", pathlib.Path("templates", n).read_text())
    pathlib.Path(sys.argv[1], n).write_text(t)
PYEOF
  for f in "$tmp/pack.tex" "$tmp/cram.tex" tests/fixtures/stress/clash.tex; do
    bash scripts/build_doc.sh "$f" --out "$tmp/out" >/dev/null 2>&1 && echo "OK   $(basename "$f")" || { echo "FAIL $(basename "$f")"; fail=1; }
  done
  bash scripts/build_doc.sh tests/fixtures/stress/overfull.tex --out "$tmp/out" >/dev/null 2>&1 \
    && { echo "FAIL overfull gate did not trigger"; fail=1; } || echo "OK   overfull gate triggers"
  rm -rf "$tmp"
else
  echo "PENDING (no TeX engine): PDF gates not run"
fi

step "plugin manifest"
if command -v claude >/dev/null 2>&1; then
  claude plugin validate . >/dev/null 2>&1 && echo "OK   claude plugin validate" || { echo "FAIL claude plugin validate"; fail=1; }
else
  echo "SKIP claude CLI not installed"
fi

step "no copyrighted material tracked"
bad="$(git ls-files 2>/dev/null | grep -Ei '\.(pdf|pptx?|docx?|djvu|epub)$' || true)"
if [ -n "$bad" ]; then echo "FAIL tracked documents:"; echo "$bad"; fail=1; else echo "OK   no PDFs/slides tracked"; fi

step "every plugin file is tracked by git (none hidden by .gitignore)"
hidden="$(git ls-files --others --ignored --exclude-standard -- .claude-plugin skills agents scripts templates 2>/dev/null | grep -v '__pycache__' || true)"
if [ -n "$hidden" ]; then echo "FAIL ignored plugin files:"; echo "$hidden"; fail=1; else echo "OK   all plugin files trackable"; fi

printf '\n'; [ $fail -eq 0 ] && echo "SELFTEST PASSED" || echo "SELFTEST FAILED"
exit $fail
