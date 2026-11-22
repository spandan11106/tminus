# Build log

## Phase 0: build-environment preflight (2026-11-22)
- User confirmed: name `tminus`, license MIT, repo at `~/tminus`, no agent attribution in commits.
- Created repo skeleton, `.gitignore`, `.venv` (pymupdf 2.1, PyYAML, Pint, pytest, reportlab).
- Fetched current plugin docs (code.claude.com: manifest-reference, components, skills, sub-agents, cli-reference, marketplace).
- Recorded tools in `docs/ENVIRONMENT.md`. Everything required is present; tectonic absent (optional).
- Gate 0: PASSED.

## Phase 1: foundations (2026-11-22)
- `.claude-plugin/plugin.json`, `marketplace.json` (single-repo, `source: "./"`), `templates/course.template.md`.
- `scripts/validate_course_md.py` (library `load`, `validate`, `load_valid`; CLI exit 0/1), 10 tests written first.
- `claude plugin validate .` passes (one warning: no icon; added in Phase 9).
- Loaded locally with `claude --plugin-dir ~/tminus plugin details tminus` (recorded in QUICKSTART).
- Gate 1: PASSED.

## Phase 2: runtime preflight, doctor, build engine (2026-11-22)
- `scripts/preflight.py`: OS detection (arch/debian/fedora/macos/wsl/windows/unknown), tiers, template
  package scan, per-OS fix commands, plugin venv install (`--install --yes`), cache + `--fast`, exit codes 0/1/2.
- Install hints verified against package indexes by a research subagent (DECISIONS 5, 6).
- 10 simulation tests: restricted PATH with stub tools, fake os-release, fake missing modules.
- `scripts/build_doc.sh`: placeholder gate, ASCII gate, latexmk -> tectonic -> pdflatex, overfull gate,
  builds in a temp dir and only moves a passing PDF; Markdown mode (+pandoc HTML if present); exit 3 when PDF is
  asked for with no engine.
- Bugs found and fixed while testing: (a) TEXINPUTS listed the templates folder before ".", so a user file named
  `pack.tex` loaded the template; "." now comes first. (b) `\degree` undefined (no gensymb); `tminus.sty`
  provides it. (c) two-line headers overlapped the first heading; headheight raised to 26pt and build_doc warns
  if the log reports headheight too small.
- `skills/doctor/SKILL.md`. Real run on this machine: all OK, exit 0. Markdown mode tested with no TeX on PATH.
- Gate 2: PASSED.
