---
name: course-context
description: "Step 1 of every tminus command except doctor. Runs the fast preflight, finds and validates course.md, and loads the professor's conventions as authoritative over the book. Use whenever a tminus command starts work on a course folder."
user-invocable: false
---

# Course context (run first)

Let `TM` be `${CLAUDE_PLUGIN_ROOT}/scripts/tm`.

0. **Course folder = the directory the session started in.** Run `pwd` once and use that absolute path for every
   later command (`cd "<path>" && ...`); never search other folders for a course. If it has no `course.md`, say
   so and suggest `/tminus:setup` there.
1. **Fast preflight.** From the course folder run `TM preflight --fast --cache-dir .tminus`.
   Exit 1: stop and tell the user to run `/tminus:doctor`. Exit 2: continue; if no TeX engine, use Markdown output.
2. **Find course.md** in the current folder (else ask for the path; suggest `/tminus:setup` if none exists).
   Run `TM validate_course_md course.md --json`. If it fails, show the errors and stop. Do not guess around them.
3. **Read course.md fully.** Keep in mind:
   - `format` (pdf or md) decides the template: `templates/*.tex` or `templates/pack.md.tmpl`.
   - **Professor conventions override the book.** When the book and the slides or the examiner disagree, use the
     convention, and say in the output which source you followed ("examiner's method, L22 slide 7; the book uses ...").
   - Given-vs-must-remember lists decide which formulas get `\examgiven` / `\examremember` (Markdown: `[given]` / `[remember]`).
   - The **verified corrections log** lists known book or slide errors. Never repeat a logged error.
4. **Page references.** The book's printed page numbers differ from PDF page numbers.
   PDF page = printed page + `page_offset`. Convert with `TM pdf_pages to-pdf <printed> --course course.md`.
   Cite printed pages to the user ("p. 141") and use PDF pages only for tools (pdftotext, crop_figure).
5. **Never silently fix the book.** If you find an error in the book or slides, flag it in the output and
   append a candidate row to `progress/corrections_candidates.md` (the recompute script does this for numbers).
   Only the user moves a candidate into the corrections log.
6. **Read source text, not memory.** Extract pages with `pdftotext -f N -l N -layout book.pdf -` (or PyMuPDF) before
   stating a fact, limit, table value or printed answer. If you cannot find the source, mark it `[UNVERIFIED]`.
