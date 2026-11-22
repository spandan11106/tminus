# PLAN.md: `tminus` Claude Code plugin (v2, sprint edition)

> **For Claude Code:** Read this whole file before doing anything. Execute the phases in order and do not skip a gate. Keep a running log in `docs/BUILD_LOG.md` (what you did, what failed, what you changed). Commit after every completed task. When something is ambiguous, pick the simplest option, record it in `docs/DECISIONS.md`, and continue. Stop to ask only at steps marked **[ASK USER]**.
>
> **Plugin name:** `tminus` (default). **[ASK USER]** to confirm in Phase 0. Keep the name in one place (`PLUGIN_NAME` in `scripts/_common.sh` and `.claude-plugin/plugin.json`) so a rename is a single edit plus a grep. Commands are invoked namespaced, e.g. `/tminus:triage`.

---

## 0. What this is, and who it is for

**One-line goal.** A shareable Claude Code plugin for a student whose exam is **2 to 3 days away** with a lot of syllabus left. It turns a raw course folder (textbook PDF, lecture slides, assignments, past papers) into a **time-budgeted plan, compact chapter packs, active-recall drills, a timed mock paper, and a night-before cram pack**, with every number verified.

**What changed from v1.** v1 generated a full document set per chapter. For a 48 to 72 hour window that is the wrong product: it produces a lot of text to reread, and the evidence says rereading is weak (section 2). v2 is organised around **triage, then drill**, not around producing documents.

**Non-goals.**
- Not a long-horizon study planner (weeks or semester). No spaced-repetition export in v1.
- Nothing course-specific inside the plugin. ME3104 Design of Machine Elements (Bhandari, page offset +24) is only the first test case.
- Never ship textbooks, professor slides or past papers (copyright). Each user supplies their own.
- No pass-probability numbers or other invented predictions. Rankings only.

**Final acceptance.**
1. Raw folder to first usable triage plan in **under 15 minutes of user attention**; to a verified chapter pack plus first drill session in **under 45 minutes**.
2. Zero unflagged numeric errors: every number in generated output was recomputed by script; every mismatch with the book or slides is flagged with an explanation.
3. The real second-course test (Phase 7) passes with no course-specific fixes needed in the plugin.
4. `scripts/selftest.sh` passes on a clean checkout, **and** `/tminus:doctor` correctly reports missing tools on a machine that lacks them (tested by simulation).

---

## 1. Lessons from the DME session the plugin must encode

| What went wrong | Becomes |
|---|---|
| Professor's slides disagreed with the book (Q2b, Q6, clutch answers changed). | `course.md` **professor-conventions** section overrides the book. Every command reads it first. |
| Book answers written from memory had errors (Ch 9 twist limits reversed). | Mandatory **verify pass** against book text and printed answers. |
| Values read by eye from a chart (A4 P3). | **Figure rule:** crop and view the figure first; any estimated value is marked `approx.`. |
| Book/slide typo (Ex 12.14: 73 °C should be 7.3 °C). | **Recompute rule:** every number recomputed in Python; mismatches go to the corrections log and are flagged in output. |
| LaTeX failures: non-ASCII characters, overfull boxes, `\given` clash, header overlap. | Hardened template plus an automated **LaTeX gate**. |
| PDF page numbers differ from printed book pages. | `course.md` stores a **page offset**; all page references go through it. |
| Examiner conventions lost between sessions. | `course.md` persists conventions and a **verified-corrections log**. |

---

## 2. Design principles from research (what shapes the feature set)

Research basis: a short literature check, mostly secondary summaries plus one primary paper. Treat the conclusions as design guidance, not proof. **Claude Code: do not cite these as established facts in user-facing text beyond what is stated here.**

1. **Practice testing and distributed practice rate highest.** Dunlosky et al. (2013, *Psychological Science in the Public Interest*) rated both as high utility, while summarisation, highlighting and rereading rated low; elaborative interrogation, self-explanation and interleaved practice rated moderate. **Implication:** the plugin's centre of gravity is `/tminus:drill` (self-testing), not long notes. Notes exist to feed drills.
2. **Distributed practice still applies inside 72 hours.** The same review notes that cramming students may not be familiar with spacing. **Implication:** the plan schedules short review blocks of earlier material on each following day, and re-plans daily from drill results.
3. **Retrieval practice is for facts; procedures need worked examples.** Several studies found retrieval practice did not beat restudying worked examples for acquiring problem-solving skill (e.g. Huang et al., 2023, *Frontiers in Psychology*, and the studies it cites), and the literature on alternating worked examples with practice problems supports mixing them. Evidence is mixed (one semester-long abstract-algebra study found testing better for long-term retention). **Implication:** `/tminus:drill` uses two modes. Theory gets question-first retrieval. Numericals get a **worked example, then a partly-completed problem, then a full problem** loop with feedback, never a blind quiz on an unseen procedure.
4. **Do not spend scarce hours on everything.** With limited time the marginal value is in what is most likely to be examined and what the student cannot yet do. **Implication:** triage first, generate material only for chapters above the cut line (lazy generation, which also saves tokens).
5. **Existing tools to be aware of (do not copy their code or text).** `PHY041/exam-prep` (a cram skill that fuses past-paper frequency with lecturer emphasis and ships a dependency probe and cost guard) and `PAIDEIA` (a per-course study graph with analysis, drilling, grading and weak-area maps). Both are MIT or similar but **verify the license before reusing anything, and default to writing everything fresh.** **Our differentiators:** professor-overrides-book conventions, page-offset handling, recompute-and-verify with a corrections log, time-budgeted triage and daily re-plan, and a preflight that degrades gracefully without LaTeX.

---

## 3. Feature decisions: keep, add, cut

### Core (build in v0.1)
| Command | Role in a 2 to 3 day sprint |
|---|---|
| `/tminus:doctor` | Preflight: checks and (with consent) installs dependencies. Also runs silently at the start of every command. |
| `/tminus:setup` | Ingest the course folder, write `course.md`; ask exam time, hours per day, self-rated strength per chapter, open or closed book, professor conventions. |
| `/tminus:triage` | Rank topics by expected marks per study minute, set the cut line for the hours available, write the day-by-day plan, re-plan daily. **New, and the heart of the plugin.** (Replaces `/exam-analyze` and `/study-plan`.) |
| `/tminus:pack <ch or tier-A>` | **Compact** chapter pack sized to a time target (default 30 to 45 minutes): 60-second snapshot, recipes, 2 to 4 worked examples, formulas, common traps. (Replaces full `/exam-notes`.) |
| `/tminus:drill` | Active-recall sessions (section 6.5). **New.** Absorbs `/theory-bank`, `/solve-assignments`, `/slide-questions` and `/check-my-answer` as question sources and grading. |
| `/tminus:formulas` | Two-column sheet plus one-page must-remember sheet. |
| `/tminus:mock` | Timed mock paper in the examiner's style with an answer key whose numbers are recomputed. Promoted from "extra" to core because it is practice testing. |
| `/tminus:cram` | Night-before pack: 1-page formulas, 1-page one-liners ordered by exam likelihood and your own weak items, top repeated mistakes, last paper solved, exam-day checklist. No new material. |

### Folded in (no separate command)
- `/align-lectures` becomes `/tminus:setup --refresh` (re-reads new lectures, updates conventions, lists every changed answer).
- `/solve-assignments` and `/slide-questions` become **question sources** for `/tminus:drill` and examples for `/tminus:pack`, tagged by chapter.
- `/check-my-answer` becomes the grading step inside `/tminus:drill`.
- Two speeds (quick and thorough) become **scope plus time budget**: triage decides how much gets generated. The verify pass is risk-based, not optional (section 5.2).

### Cut for this product (log in `docs/IDEAS.md` for a possible v2)
- Anki export: needs weeks of spacing to pay off; the drill queue covers a 72-hour window.
- Full-chapter prose notes, summaries, mind maps, highlighted books: low-utility rereading material.
- Podcast or audio summaries, pomodoro timers, streaks and gamification: not evidence-backed and not core.
- Pass-probability or score estimates: cannot be justified from the data available.

### Candidate v0.2 (only after the Phase 7 gate)
- Handwritten answer photo grading via the model's vision.
- `/tminus:reflect`: end-of-day review of the error log with a short plan tweak.
- Optional Anki export for users with a longer horizon.

---

## 4. Repository layout (create exactly this)

```
tminus/
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json            # optional, for sharing
├── commands/
│   ├── doctor.md
│   ├── setup.md
│   ├── triage.md
│   ├── pack.md
│   ├── drill.md
│   ├── formulas.md
│   ├── mock.md
│   └── cram.md
├── skills/
│   ├── course-context/SKILL.md     # load and obey course.md
│   ├── verify-pass/SKILL.md        # risk-based verification procedure
│   ├── figure-handling/SKILL.md    # crop, view, confirm, cite
│   └── drill-method/SKILL.md       # retrieval vs worked-example loop rules
├── agents/
│   ├── verifier.md                 # independent fact and number check
│   └── recomputer.md               # recompute numerics in Python
├── templates/
│   ├── course.template.md
│   ├── pack.tex
│   ├── cram.tex
│   ├── pack.md.tmpl                # Markdown output path (no-LaTeX mode)
│   └── briefs/                     # one brief per command, tunable without editing commands
├── scripts/
│   ├── _common.sh
│   ├── preflight.py                # the dependency checker (section 5.0)
│   ├── build_doc.sh                # engine abstraction: latexmk, tectonic, or Markdown-only
│   ├── check_ascii.py
│   ├── check_overfull.py
│   ├── pdf_pages.py
│   ├── crop_figure.py
│   ├── recompute.py
│   ├── validate_course_md.py
│   ├── triage_score.py             # transparent scoring, unit-tested
│   ├── drill_state.py              # attempts log, error log, weakmap, queue
│   └── selftest.sh
├── tests/
│   ├── fixtures/                   # make_toycourse.py plus generated SYNTHETIC course
│   └── test_*.py
├── docs/ (BUILD_LOG.md, DECISIONS.md, ENVIRONMENT.md, IDEAS.md, QUICKSTART.md)
├── examples/course.example.md
├── .gitignore                      # courses/, .tminus/, outputs/, LaTeX aux files
├── LICENSE
├── requirements.txt
└── README.md
```

**Before writing any plugin file:** fetch the current Claude Code documentation for plugins, slash commands, skills, subagents and hooks (docs.claude.com) and confirm manifest fields, command frontmatter and directory conventions. If the docs differ from this layout, follow the docs and log it in `docs/DECISIONS.md`.

**Per-course working folder** (lives outside the plugin, e.g. `courses/ME3104/`):

```
course.md
.tminus/preflight.json              # cached doctor result
sprint/triage.md   sprint/plan.md   # ranking and day-by-day plan
packs/              mock/            cram/
progress/attempts.jsonl  progress/errors.md  progress/weakmap.md
```

---

## 5. Cross-cutting systems

### 5.0 Preflight and dependency check (BUILD IT FIRST, run it always)

There are **two layers**, and both are required.

**Layer A: build-environment preflight (Phase 0, before Claude Code builds anything).**
Check and record in `docs/ENVIRONMENT.md`: `python3 >= 3.9`, `git`, `pip` and `venv` module, a TeX engine (`latexmk` plus `pdflatex`, or `tectonic`), `pdftoppm` (poppler) or PyMuPDF, network access to the docs site, free disk space (at least 1 GB). Rules:
- Create a project virtualenv (`python3 -m venv .venv`) and install Python dependencies there. **Never** use `pip install --break-system-packages` and never touch system Python (many distros, including Arch and recent Debian and Ubuntu, mark it externally managed).
- If something is missing, print the exact install command for this OS and **[ASK USER]** before running anything that needs `sudo`. Never run `sudo` silently.
- If the user declines to install TeX, continue the build but mark every PDF gate as `PENDING (no TeX engine)` in the build log. **Do not claim those gates passed.**

**Layer B: runtime preflight inside the plugin (`scripts/preflight.py`, surfaced as `/tminus:doctor`).**
This runs on the end user's machine, which may have none of the tools. Requirements:

1. **OS detection:** read `uname` and `/etc/os-release`; classify as Arch, Debian or Ubuntu, Fedora, macOS, WSL, or native Windows (best effort, recommend WSL2).
2. **Tiers:**
   - *Required:* `python3 >= 3.9`; a PDF text extractor (PyMuPDF or `pdftotext`).
   - *Required for PDF output, otherwise degrade:* a TeX engine (`latexmk` with `pdflatex`, or `tectonic`) and every LaTeX package the shipped templates use. **Derive that package list by scanning `templates/*.tex` for `\usepackage{...}`** and test each with `kpsewhich <name>.sty` (skip the package test for `tectonic`, which fetches packages itself).
   - *Optional:* `pdftoppm`, `pint`, `genanki`, `pytest` (tests only).
3. **Python dependencies** are checked by import and installed into a plugin-owned virtualenv (default `~/.cache/tminus/venv`, overridable), never globally.
4. **Output:** a short table (`OK`, `MISSING`, `WARN`), the tier of each item, and for each gap the **exact fix command for the detected OS**. Include install commands for Arch (`pacman`), Debian and Ubuntu (`apt`), Fedora (`dnf`), macOS (`brew`, including a lightweight `tectonic` option), and WSL (same as Ubuntu). **Verify every package name against current distro documentation before hardcoding it, and mark any you could not verify as `UNVERIFIED` in `docs/DECISIONS.md`.**
5. **Consent:** `/tminus:doctor --install` may install Python packages into the plugin venv automatically after one confirmation, but it only **prints** system-level commands (anything needing `sudo` or a package manager) and asks the user to run them or approve them one by one.
6. **Graceful degradation (important for a sprint tool).** If no TeX engine is available and the user does not want one, set `format: md` and every command still works, producing Markdown (and HTML if the environment has a converter). The LaTeX gates simply do not apply. **The tool must never fail a student at 2 a.m. because LaTeX is missing.** `scripts/build_doc.sh` is the single place that chooses `latexmk`, then `tectonic`, then Markdown-only, and reports which it used.
7. **Caching:** write `.tminus/preflight.json` with timestamp, OS class, tool versions and results. Every command begins with a fast check (a few `command -v` calls, under one second). A full re-check runs if the cache is older than 7 days, if any cached tool has disappeared, or on `/tminus:doctor`.
8. **Exit codes:** 0 all required present, 1 required missing, 2 only optional or degradable items missing.
9. **Tests:** simulate missing tools by running `preflight.py` with a restricted `PATH` and a fake `/etc/os-release` fixture. Cover: everything present, no TeX, no Python deps, unknown OS, a missing LaTeX package. Assert that the right fix commands appear and that exit codes are correct.

### 5.1 `course.md` schema (build before any command)

```markdown
---
course_code: ME3104
course_name: Design of Machine Elements
schema_version: 2
exam_datetime: 2026-11-25T09:30     # used to compute hours left
hours_per_day: 6                    # study hours available per day
book_policy: closed                 # closed | open | formula-sheet-allowed
format: pdf                         # pdf | md   (set by doctor if no TeX)
exam_pattern: |
  Section A one-liners with bracketed options; Section B numericals with printed formulas
---

## Book
- path: book/bhandari.pdf
- page_offset: 24                   # pdf_page = printed_page + offset

## Chapters
| id | title | book pages (printed) | lectures | assignments | past papers | self-rating (1-5) |
|----|-------|----------------------|----------|-------------|-------------|--------------------|

## Professor conventions (OVERRIDE THE BOOK)
- (topic, what he does, source, date added)

## Given vs must-remember formulas
## Verified corrections log
| date | location | book/slide says | correct value | how verified |
```

**Tasks:** write `templates/course.template.md`; write `scripts/validate_course_md.py` (front matter fields, paths exist, integer offset, every chapter row has id and title, rating in 1 to 5, required sections present); write `tests/test_validate_course_md.py` covering valid, missing book, bad offset, empty chapter table, bad rating.

### 5.2 Verification rules (skills: `course-context`, `verify-pass`, `figure-handling`)

**`course-context`** (step 1 of every command except `doctor`):
1. Run the fast preflight, then locate `course.md` and run `validate_course_md.py`. Refuse to continue on failure.
2. Load professor conventions as **authoritative**; when book and slides conflict, conventions win and the output names the source used.
3. Convert every page reference through the page offset.
4. Never silently fix an error found in the book or slides: append to the corrections log.

**`verify-pass`** (last step of every command that emits facts or numbers). Risk-based, always on:
1. **Always:** recompute every number via `scripts/recompute.py`; check every formula and every limit or range against the cited book or slide page; compare with printed book answers where they exist.
2. **Sample or skip:** descriptive prose.
3. End the deliverable with a **Verification report**: checked, matched, flagged, unverifiable. Anything unverifiable is marked `[UNVERIFIED]` and never stated as fact.
4. When a command generates for more than 3 chapters or a mock paper, also run the independent `verifier` subagent.

**`figure-handling`:** crop with `crop_figure.py`, **view the image**, read values only after viewing, mark every read-off value `approx.` with the method stated, prefer a tabulated value when one exists.

### 5.3 Scripts to implement (all with tests)

| Script | Requirements |
|---|---|
| `check_ascii.py` | Scan `.tex`; report file, line, column, offending character and the LaTeX-safe replacement; exit 1 if any. |
| `check_overfull.py` | Parse the LaTeX `.log`; report `Overfull \hbox` and `\vbox` over a threshold (default 1 pt); exit 1 if any. |
| `build_doc.sh` | Engine abstraction. If `format: pdf`: ASCII gate, build with `latexmk` (fallback `tectonic`, fallback `pdflatex` twice), overfull gate. If `format: md`: render the Markdown template. Never leave a half-built file in `outputs/`. Print which engine ran. |
| `pdf_pages.py` | Printed to PDF page and back via the offset. Library plus CLI. |
| `crop_figure.py` | Render a page (PyMuPDF preferred) and crop to coordinates or a detected caption; write PNG. |
| `recompute.py` | Takes a list of `{id, expression or snippet, inputs, claimed_value, units, tolerance}`; evaluates with `pint` if available; prints `OK` or `MISMATCH` with computed vs claimed; appends candidate corrections to a file for the user to confirm. Never edits `course.md` itself. |
| `triage_score.py` | Pure, deterministic scoring (section 6.2). Unit-tested on the toy course so rankings are reproducible and explainable. |
| `drill_state.py` | Append to `attempts.jsonl`, regenerate `errors.md` and `weakmap.md`, compute the review queue. Unit-tested. |
| `validate_course_md.py`, `preflight.py` | See 5.1 and 5.0. |
| `selftest.sh` | Runs unit tests, preflight simulation, toy-course builds and gates; non-zero on any failure. |

**Template hardening (`pack.tex`, `cram.tex`):** define the given-marker under a namespaced macro (`\examgiven`) and test that the template compiles in a document that also defines `\given`; `fancyhdr` with a large enough `\headheight` and a long-title test; two-column formula environment and a one-page formulas-only environment with font-shrink fallback; `\flag{...}` for book or slide error callouts and `\approxval{...}` for chart reads; no course-specific text anywhere.

---

## 6. Command specifications

Every command file has YAML frontmatter (`description`, `argument-hint`, `allowed-tools` as appropriate) and a numbered procedure. Briefs live in `templates/briefs/<name>.md`. Every command starts with `course-context` and ends with `verify-pass`, except `doctor` and `setup` (which ends with `validate_course_md.py`).

### 6.1 `/tminus:setup [--refresh]`
1. Run preflight; if `format` is undecided, let `doctor` set it.
2. Inventory the folder: classify book, slides, assignments, past papers by filename **and content sniffing**; show the inventory and list anything unclassified. Detect image-only (scanned) PDFs and tell the user OCR is needed; do not silently degrade.
3. **Page offset:** find a page with a printed number, compute the offset, confirm on two more pages.
4. Extract the table of contents into the chapter list; map lectures, assignments and past-paper questions to chapters by content; mark low-confidence mappings.
5. **[ASK USER]**, in one short batch: exam date and time, study hours per day, open or closed book and what is provided, a 1 to 5 self-rating per chapter, and "where does your professor's method or notation differ from the book, and what did he stress in class?" Record the answers.
6. Draft the given-vs-must-remember formula lists from past-paper front matter if present.
7. Write `course.md`, run the validator, print only the low-confidence items.
- `--refresh`: re-read new or changed lectures, update conventions, and list **every answer or recipe that changed** because of them.

**Done when:** the validator passes and the user has seen the low-confidence list.

### 6.2 `/tminus:triage`
**Inputs:** `course.md`, past papers, slide emphasis signals, self-ratings, and (after day 1) `weakmap.md`.
**Scoring (documented in `docs/TRIAGE.md`, implemented in `triage_score.py`):**
- *Expected marks* per topic: marks across past papers, recency-weighted, plus a small bonus for lecturer emphasis (slide count, "important" or "exam" flags, assignment density) and for the topic appearing in the stated exam pattern.
- *Study cost* in minutes: estimated from page count and difficulty class.
- *Gap*: how far the student is from competent, from self-rating and then drill results.
- *Priority* = expected marks × gap ÷ study cost.
**Output (`sprint/triage.md`):**
1. A ranked table with **tiers**: A must do, B should do, C if time, X skip. Show the cut line for the hours available and say plainly what the cut costs in expected marks.
2. A one-line **reason** per topic (so the student can disagree and edit weights).
3. A **day-by-day plan** (`sprint/plan.md`) with timed blocks: new material, drill, and a short **spaced review of the previous day's material** each day; the last block of the final full day is a timed mock; a sleep reminder before the exam.
4. Warnings that matter: a choice-based paper ("answer any 5 of 7") lowers the coverage needed; a topic that appears only once may be a fluke.
**Rules:** rankings are heuristics, labelled as such; no percentages or pass odds; marks per paper must sum to the paper total (checked in code, mismatches flagged). **Re-run daily**: it reads drill results and rewrites the remaining plan, saying what moved and why.

### 6.3 `/tminus:pack <chapter | tier-A>`
Generate only for chapters the user names or for tier A. Target study time defaults to 30 to 45 minutes per chapter and is printed on the first page and used by the plan.
**Fixed structure:** (1) 60-second snapshot of what is most examinable; (2) recipes, one per numerical question type, as numbered steps in the **professor's method**; (3) two to four worked examples, professor-style first, each recomputed; (4) the chapter's formulas with units and the given or must-remember marker; (5) **common traps**, pulled from the corrections log and `errors.md`; (6) a pointer to the matching `/tminus:drill` command.
**Rules:** no long theory prose (theory goes into the drill deck as one-liners); figures per the figure rule; ends with a verification report; built with `build_doc.sh`.

### 6.4 `/tminus:formulas`
Two-column sheet across chosen chapters (formula, when to use, symbols and units, given or must-remember marker) plus a **one-page must-remember** sheet. Units on every formula; at least one dimensional check per formula group via `recompute.py`.

### 6.5 `/tminus:drill [chapter | weak | mixed] [--minutes N]`
The active-recall engine. Interactive in the terminal; state in `progress/`.
**Theory and facts (retrieval mode):**
- Ask first, **wait for the student's answer**, then reveal and grade against the book or slide with the professor's wording winning. Question types: one-liners with bracketed options, fill in the blank, true or false, short answer.
- Wrong or hesitant items are re-queued later in the same session and on the next day.
**Numericals (worked-example loop):** for each recipe, show a worked example, then a **partly completed** problem, then a **full** problem with new numbers; give feedback on method first (against professor conventions), then check the numbers with `recompute.py`. Hints on request; never reveal the answer before an attempt unless the student types `skip`.
**Sources:** past-paper questions, assignment problems and slide examples (all tagged by chapter), plus generated variants with fresh numbers.
**Modes:** `chapter` (focused), `weak` (from the weakmap), `mixed` (interleaves chapters, used from day 2).
**State:** every attempt is appended to `attempts.jsonl`; `errors.md` is a human-readable list of **mistakes the student keeps making** (feeds the traps section and the cram pack); `weakmap.md` ranks topics and feeds `triage`.
**Rules:** sessions are timeboxed; end with a 3-line summary and a suggestion for the next session, with no padding and no streaks or points.

### 6.6 `/tminus:mock [--minutes N]`
Generate a timed mock paper in the examiner's exact style from `exam_pattern` (marks distribution mirrors triage's analysis), **with new numbers, not copied past-paper text**, plus an answer key and marking scheme. **Every numeric answer is recomputed and the independent verifier runs**, because a wrong answer key does more harm than no mock. Offer to run the grading as a `drill` review.

### 6.7 `/tminus:cram`
Night-before and morning-of pack: one page of must-remember formulas; one page of one-liners ordered by exam likelihood and the student's own weak items; the top 10 repeated mistakes from `errors.md`; last year's paper solved in exam style; an exam-day checklist (units, what is provided, what is closed book). **No new material.** Verify pass runs in full.

### 6.8 `/tminus:doctor [--install]`
Runs `preflight.py` and shows the table and fix commands (section 5.0). Also records the chosen output format.

---

## 7. Subagents
- `verifier`: given a draft and its sources, re-derive each claim from the sources **without seeing the draft's reasoning**; return a table of claim, source location, match status.
- `recomputer`: given a list of numeric claims, write and run the Python, return OK or MISMATCH.
Keep prompts short, tool access minimal (read files, run Python), and output machine-parseable.

---

## 8. Test fixtures (synthetic only)

`tests/fixtures/make_toycourse.py` generates, reproducibly, a fake course in a made-up subject: a ~30-page book PDF with a known offset (+6) and a printed-answers section containing **planted errors** (a reversed limit, a decimal-point typo, a wrong printed answer); three slide PDFs, one **contradicting the book** (to test the conventions override); two assignment PDFs; two past papers with known mark totals; and `course.expected.md`. List the planted errors in `tests/fixtures/PLANTED_ERRORS.md`.

**Toy-course acceptance:**
- `setup` matches `course.expected.md` on offset, chapter mapping and conventions.
- `triage` ranking matches the hand-computed expected ranking in `tests/`.
- `pack`, `formulas`, `mock` and `cram` build in both `pdf` and `md` formats and pass their gates.
- The verify pass flags **every planted error**.
- `drill` state tests: a wrong answer is re-queued, `weakmap` order changes, and `triage` reacts on re-run.

---

## 9. Phases and gates (do not start a phase until the previous gate passes)

**Phase 0: Build-environment preflight** (section 5.0 Layer A)
- **[ASK USER]** confirm the plugin name (default `tminus`) and the license (default MIT); approve any system installs.
- Create the repo skeleton, `.gitignore`, venv, `docs/ENVIRONMENT.md`.
- **Gate 0:** `docs/ENVIRONMENT.md` lists every required tool as present, or as missing with the user's decision recorded; PDF gates are marked pending if no TeX engine.

**Phase 1: Foundations:** manifest, `course.md` schema, template, validator and tests.
- **Gate 1:** validator tests pass; the plugin loads locally by the documented method (record the exact command in `docs/QUICKSTART.md`) and lists its commands.

**Phase 2: Preflight (runtime)** (section 5.0 Layer B) and `/tminus:doctor`, plus `build_doc.sh` engine abstraction.
- **Gate 2:** all simulated-environment tests pass; on this machine `doctor` reports correctly; Markdown-only mode produces output with no TeX engine on `PATH`.

**Phase 3: Scripts and templates** (section 5.3): ASCII and overfull checks, page helper, figure crop, recompute, triage scoring, drill state.
- **Gate 3:** all script tests pass; the template compiles on a stress document (long title, non-ASCII that must be rejected, `\given` clash, overfull-prone table).

**Phase 4: Skills and subagents** (sections 5.2 and 7) and the briefs.
- **Gate 4:** each skill file is linted for length and clarity; the subagent output formats parse in tests.

**Phase 5: Core commands** (section 6) in this order: `setup`, `triage`, `pack`, `drill`, `formulas`, `mock`, `cram`.
- **Gate 5:** the full toy-course run passes every acceptance item in section 8 in both output formats.

**Phase 6: Dry run** (self-test in sprint conditions): script a 48-hour scenario on the toy course (day 1 triage and packs, day 2 drill plus re-plan, last day mock and cram) and record wall-clock time and token use per command in `docs/BUILD_LOG.md`.
- **Gate 6:** time to first triage plan under the section 0 targets; any command that is slow or heavy is tightened (smaller scope, lazy generation) before moving on.

**Phase 7: Real second-course test** **[ASK USER]**
- Ask for a real course folder (e.g. Heat Transfer or Dynamics of Machinery). Run `doctor`, `setup`, `triage`, `pack` on tier A, `drill`, `mock`, `cram`.
- Log everything that breaks or is course-specific; **fix it in the plugin, not in the outputs.**
- **Gate 7:** the user confirms the pack and triage needed no manual restructuring. If the user is unavailable, mark pending and proceed only to Phase 9.

**Phase 8: v0.2 candidates** (only after Gate 7, in the section 3 order, one at a time with its own test).

**Phase 9: Packaging**
- README: what it does and who it is for (exam in 2 to 3 days), a **Requirements** section that mirrors `doctor`, a three-step quick start (`/tminus:doctor`, `/tminus:setup`, `/tminus:triage`), the verification philosophy, the triage heuristic and its limits, and an explicit copyright statement.
- `examples/course.example.md` with dummy content; `docs/QUICKSTART.md` verified by following it from a clean clone **on a machine or container without TeX**.
- Scan the repo to confirm no copyrighted material is committed (no PDFs except generated toy fixtures; `courses/` ignored).
- **Gate 9:** clean clone, `scripts/selftest.sh` passes, quick start works in both formats.

---

## 10. Rules of engagement for Claude Code
1. **Test first** for every script: write the test, watch it fail, implement, watch it pass.
2. **Small commits**, one task each, message format `phaseN: <what>`.
3. **No silent deviations:** every change from this plan goes in `docs/DECISIONS.md` with the reason.
4. **No copyrighted content** in the repo. If you find yourself writing out textbook passages, stop and use synthetic text. Do not copy code or prompts from other exam-prep projects.
5. **No unconsented installs, no silent `sudo`, no global pip.** Use the venv.
6. **Keep it simple:** Python 3 with a small dependency list (`pymupdf`, `pint`, `pyyaml`, `pytest`, `reportlab` for fixtures). Pin versions in `requirements.txt`.
7. **Fail loudly** with readable errors and non-zero exit codes; never swallow exceptions.
8. **Do not over-build:** a feature not in this plan goes to `docs/IDEAS.md`.
9. **Report at each gate** with a short block: passed, failed, pending, next.
10. **Trust current docs over this file** for plugin format, tool names and flags, and log the difference.

---

## 11. Risks and mitigations
| Risk | Mitigation |
|---|---|
| Model invents book content | Verify pass, recompute rule, `[UNVERIFIED]` marking, planted-error tests |
| Triage ranks wrongly (one-off topics, changed syllabus) | Transparent per-topic reasons, user-editable weights, rankings labelled heuristic, daily re-plan from drill results |
| Student reads packs instead of drilling | Pack ends with a drill pointer; the plan allocates more time to drill than to packs |
| Drill on unseen procedures frustrates or teaches nothing | Worked-example loop before any blind numerical |
| Wrong mock answer key | Recompute every key number and run the verifier subagent |
| Missing LaTeX on the user's machine | Preflight, graceful Markdown mode, exact per-OS fix commands, tested by simulation |
| Professor conventions missed | `setup` asks explicitly; `setup --refresh` re-checks; conventions win in every command |
| Scanned PDFs without text | `setup` detects and tells the user OCR is needed |
| Token and time cost on a big book | Lazy generation (only tier A on request), scope printed before long runs |
| Over-building before the core is proven | Gate 7 blocks Phase 8 |

---

## 12. Definition of done
- [ ] Gates 0 to 7 and 9 passed (Gate 7 either passed by the user or recorded as pending)
- [ ] `scripts/selftest.sh` passes on a clean clone, with and without a TeX engine
- [ ] `/tminus:doctor` correctly reports a machine missing tools (simulated) and gives the right fix commands
- [ ] Toy-course run catches every planted error
- [ ] 48-hour dry run meets the time targets in section 0
- [ ] No copyrighted material in the repo
- [ ] `README.md`, `docs/QUICKSTART.md`, `examples/course.example.md` complete
- [ ] `docs/BUILD_LOG.md`, `docs/DECISIONS.md`, `docs/ENVIRONMENT.md` up to date
- [ ] Final status report printed: what was built, what is pending, known limitations
