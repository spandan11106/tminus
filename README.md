# tminus

**Exam in 2-3 days and a lot left to cover?** `tminus` is a Claude Code plugin that turns your own course folder
(textbook PDF, lecture slides, assignments, past papers) into:

- a **triage plan**: topics ranked by expected marks per study minute, a cut line for the hours you have, and a
  day-by-day schedule with spaced review, a timed mock and a cram block;
- **compact chapter packs** (30-45 min each): snapshot, recipes in your professor's method, worked examples,
  formulas marked *given* or *remember*, common traps;
- **active-recall drills** in the terminal: retrieval for theory, worked example -> completion -> full problem for
  numericals, with your mistakes logged and fed back into the plan;
- a **mock paper** in your examiner's style with a verified answer key;
- a **night-before cram pack**.

Every number in the output is recomputed in Python, and every disagreement with the book or slides is flagged
with an explanation.

## Requirements
`/tminus:doctor` checks all of this and prints the exact install command for your OS.

| | needed for | |
|---|---|---|
| Python >= 3.9 with PyYAML | everything | required |
| PyMuPDF or `pdftotext` (poppler) | reading PDFs | required |
| TeX: `latexmk` + `pdflatex` (TeX Live) or `tectonic` | PDF output | optional: without it, output is Markdown |
| `pdftoppm` or PyMuPDF | figure crops | optional |
| Pint | unit-aware recompute | optional |

Python packages go into a plugin-owned virtualenv (`~/.cache/tminus/venv`, set by `/tminus:doctor --install`).
Nothing is installed globally, and nothing that needs `sudo` is ever run for you. Native Windows: use WSL2.

## Quick start
```
/plugin marketplace add <owner>/tminus
/plugin install tminus@tminus-marketplace
```
Then, in your course folder:
1. `/tminus:doctor`: check the machine (say yes to Markdown mode if you have no LaTeX).
2. `/tminus:setup`: classify files, find the book's page offset, map lectures, assignments and past-paper
   questions to chapters, and ask you a few questions (exam time, hours per day, self-ratings, and how your
   professor differs from the book).
3. `/tminus:triage`: get the ranking, the cut line and today's plan.

Then follow the plan: `/tminus:pack <chapter>`, `/tminus:drill [chapter|weak|mixed]`, `/tminus:formulas`,
`/tminus:mock`, and `/tminus:cram` the night before. Re-run `/tminus:triage` each morning.
See `docs/QUICKSTART.md` for loading from a clone.

## How it stays correct
- **Your professor wins.** `course.md` has a professor-conventions section; every command follows it over the book
  and says which source it used.
- **Recompute rule.** Every number goes through `scripts/recompute.py`; mismatches with the book become flags
  and candidate rows for your corrections log (you confirm them).
- **Source rule.** Formulas, limits and table values are checked against the cited page; page numbers go through
  the book's page offset. Anything unchecked is marked `[UNVERIFIED]`.
- **Figure rule.** Figures are cropped, viewed, then used; chart reads are marked *approx.*
- **Independent verifier** subagent for mock papers and multi-chapter outputs.
- Each output ends with a verification report: checked, matched, flagged, unverifiable.

## How triage works, and its limits
`priority = expected marks x gap / study minutes`, with expected marks from recency-weighted past papers plus a
small bonus for lecture emphasis, and the gap from your self-rating and then your drill accuracy. All formulas and
weights are in `docs/TRIAGE.md` and editable per course. It is a heuristic: past papers are a small sample and
syllabi change. There are no pass probabilities or predicted scores, by design.

## Why drills and not long notes
Practice testing and spaced practice are among the best-supported study techniques; rereading and highlighting are
among the weakest (Dunlosky et al., 2013). For problem-solving, worked examples alternated with practice beat blind
quizzing on an unseen procedure. So packs are short and exist to feed drills.

## Copyright
This repository contains **no textbooks, slides or past papers**, and must never contain them. You supply your own
course files; all outputs stay in your course folder. Test fixtures are synthetic (`tests/fixtures/make_toycourse.py`).

## Development
```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
scripts/selftest.sh            # add --no-tex to test Markdown mode
claude plugin validate .
```
Design and decisions: `docs/PLAN.md`, `docs/DECISIONS.md`, `docs/BUILD_LOG.md`.

MIT licence.
