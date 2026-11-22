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

## Phase 3: scripts and templates (2026-11-22)
- `check_ascii.py`, `check_overfull.py`, `pdf_pages.py`, `recompute.py` (safe AST eval, math whitelist,
  optional `snippet`, pint units, 1 % default tolerance, decimal-slip note, candidate-corrections file),
  `triage_score.py` (+ `docs/TRIAGE.md`), `drill_state.py`, `crop_figure.py` (caption detection, bbox in pt
  or fractions, pdftoppm fallback), `selftest.sh` (with `--no-tex`).
- Tests written before each implementation (except preflight, see DECISIONS 8).
- Triage: first version reserved the full 120 min mock while the plan shortened it, leaving ~80 idle min and
  skipping a chapter; budget and plan now share `mock_slot()` (hand-computed test updated).
- `templates/tminus.sty`: namespaced macros (`\examgiven`, `\examremember`, `\flag`, `\approxval`,
  `\unverified`, `\tmans`), boxes, `tmsheet` (2-col) and `tmonepage` (dense 1-page) environments.
- Stress document (long header, user `\given` + `remember` env, markers) compiles; overfull table fails the
  gate and leaves no PDF; non-ASCII rejected with replacement hints.
- `selftest.sh`: PASSED with TeX (60 tests) and with TeX hidden (PDF gates PENDING, as designed).
- Gate 3: PASSED.

## Phase 4: skills and subagents (2026-11-22)
- Internal skills `course-context`, `verify-pass`, `figure-handling`, `drill-method` (`user-invocable: false`).
- Agents `verifier` (sonnet; re-derives claims from sources, fenced-json output: MATCH / MISMATCH / SOURCE_ERROR /
  NOT_FOUND) and `recomputer` (haiku; wraps recompute.py). `scripts/agent_output.py` parses both (tests).
- Briefs in `templates/briefs/` (setup, triage, pack, drill, formulas, mock, cram); `templates/pack.md.tmpl`.
- `tests/test_skill_lint.py`: frontmatter, description length, body <= 900 words, user-invocable flags, agents
  declare a json output block. YAML descriptions containing ": " had to be quoted (caught by the lint).
- Gate 4: PASSED.

## Phase 5: core commands (2026-11-22)
- Command skills `setup`, `triage`, `pack`, `drill`, `formulas`, `mock`, `cram`, each starting with course-context and
  ending with verify-pass; `allowed-tools` pre-approves only the `tm` wrapper.
- Synthetic toy course (`tests/fixtures/make_toycourse.py`, by a subagent; planted errors in
  `tests/fixtures/PLANTED_ERRORS.md`): offset +6, reversed twist limit, 73 vs 7.3 C, wrong printed answer 47.7 vs
  74.6 MPa, L02 slide contradicting the book (stress area vs nominal area).
- `tests/test_toycourse_pipeline.py`: hand-computed toy ranking 4, 3, 1, 2; 6 wrong drill attempts on ch 2 move it
  to the top on re-triage.

## Phase 6: dry run on the toy course (headless `claude -p --plugin-dir`, model sonnet, 2026-11-22)
| command | wall time | cost (USD) | result |
|---|---|---|---|
| /tminus:setup | 58 s | 0.27 | offset 6 (3 pages checked), all mappings match course.expected.md, L02 convention recorded, **all 3 planted book errors found** |
| /tminus:triage | 20 s | 0.14 | ranking 4, 3, 1, 2 (= hand computation), plan written |
| /tminus:pack 4 (pdf) | 80 s | 0.34 | 3 pages, 12/12 numbers recomputed, planted 73 C error flagged, deck of 22 items |
| /tminus:pack 3 (md) | 68 s | 0.26 | professor's A_t convention used over the book (C 0.2314 vs book 0.288), 23/23 recomputed |
| /tminus:drill 4 (4 turns via --resume) | ~30 s compute | 0.24 | ask-wait-grade-log loop, partial answers logged with mistake notes, errors.md + weakmap rebuilt |
| /tminus:mock (pdf) | 116 s | 0.54 | 50 marks in examiner style, new numbers; verifier 18/18 MATCH |
| /tminus:formulas (pdf) | 172 s | 0.65 | 2-page sheet + 1-page must-remember; verifier 37 claims, confirmed all planted errors |
| /tminus:cram (pdf) | 89 s | 0.39 | 4 pages; weak ch 4 items first; 2024 paper solved |
| /tminus:doctor | 11 s | 0.10 | correct table; tm calls ran without prompts |
| /tminus:formulas (md) | 80 s | 0.37 | Markdown sheets; dimensional checks done by hand because pint was absent (no plugin venv yet) |
| /tminus:mock (md) | 118 s | 0.51 | Markdown paper + key; recompute 35/35; verifier 18/18 |
| /tminus:cram (md) | 109 s | 0.50 | Markdown cram pack; noticed the corrections-log page cite (p.22 vs p.23) left by setup |

Total for the full toy sprint (12 runs): about 17 min of compute and USD 4.3 on sonnet.

Time to first triage plan: about 80 s of compute plus answering one question batch, far under the 15-minute
target. Verified pack + first drill: under 5 minutes of compute (target 45 min).

Problems found by the dry run and fixed in the plugin (not in the outputs):
1. Past-paper labels like `Q1(iv)` rejected by the validator; `A1 (P1, P2)` split at the inner comma. Fixed + tests.
2. A nested run looked for course.md in the wrong folder; course-context now pins the folder with `pwd`.
3. Setup wrote book errors straight into the verified corrections log; it now writes candidates and asks.
4. `.gitignore` hid `skills/mock` and `skills/cram`; anchored patterns, selftest now checks for hidden plugin files.
5. Cram one-page sheets put the section title inside the 3-column block (hyphenated title); `tmonepage` takes a
   full-width title argument. Layout previews go to `.tminus/`.
6. Mock printed the key path before the attempt; it now reveals the key only after the student finishes.
7. Doctor's compound shell line was refused by permissions; doctor now runs one command at a time.
8. In the md mock run the model typed the verifier's statuses into a file by hand (placeholder evidence). The
   verifier now writes its own JSON to a path it is given; skills must never write that file.
9. Without the plugin venv, `tm` falls back to system python3 (no pint): checks still ran, but unit-aware. The
   doctor's `--install` covers this; noted in the README requirements.

Known limitation: Markdown output cannot guarantee "one printed page" for the cram and must-remember pages.
Gate 5: PASSED (setup matched expected; triage matched hand ranking; pack/formulas/mock/cram built in pdf and md;
every planted error flagged; drill state re-queues, reorders the weakmap and moves triage).
Gate 6: PASSED (time targets met by a wide margin; heavy commands are formulas and mock at ~2-3 min).
