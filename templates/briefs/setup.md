# Brief: setup (tunable)

## Inventory and classification
Classify every PDF/PPTX in the course folder (recursively, skip `.tminus/`, `sprint/`, `packs/`, `mock/`, `cram/`,
`progress/`, `outputs/`) by filename **and** first-page text:
- **book**: many pages (> 80), a contents page, "Chapter" headings, printed page numbers.
- **slides**: landscape pages, few words per page, "Lecture"/"L<nn>" in the name or title.
- **assignment**: "Assignment", "Tutorial", "Problem set", "Homework", numbered problems, no marks table.
- **past paper**: "Examination", "End semester", "Mid semester", "Quiz", marks in brackets, time allowed, total marks.
- **unclassified**: list for the user; never guess silently.
Scanned PDFs: run `TM pdf_text <file> --scan` on every PDF. Report "image-only" and "partly scanned" files to the
user. If tesseract is present, `TM pdf_text <file> --pages N` OCRs those pages on demand (slow: only the pages you
need). If not, tell the user OCR is unavailable (`/tminus:doctor` gives the install command). Never continue with
a scanned file silently. Prefer a text copy of the same document when one exists (duplicates are common).

## Page offset
Find three body pages whose printed number you can read in the header or footer (`pdftotext -f N -l N -layout`).
offset = pdf_page - printed_page. All three must agree; if not, report the pages and ask.

## Chapters
From the contents page(s): chapter id (the book's own number), title, printed page range. Keep only chapters in
the syllabus: ask the user which ones are examinable if the book has more.

## Mapping lectures, assignments, past-paper questions to chapters
By content (keywords, formulas, figure types), not filename alone. For each mapping note a confidence
(high/medium/low). Past-paper cells use the exact format `<paper> <question> (<marks>)`, separated by `;`,
e.g. `2024 Q2b (6); 2024 Q1(iv) (1)`. Split a mixed question (Q1 one-liners) across chapters part by part.
Check: the tagged marks of each paper add up to its total (`paper_total`).
Record every past paper under `papers:` in the front matter with its `year`. Midsems, quizzes and papers whose
questions are partly out of scope get `partial: true` and a lower `weight` (default 0.5); papers with a different
total get `total:`. Triage uses these for recency weights and the totals check.

## Emphasis signals (for triage)
Write `sprint/signals.json`: `{"<chapter id>": {"slides": n, "flags": n, "assignments": n, "in_pattern": bool,
"kind": "theory|numerical|mixed"}}`. `flags` = slides marked important/exam/"will be asked"/starred.

## Questions to ask (one batch)
1. Exam date and start time. 2. Study hours per day. 3. Open/closed book; what is printed on the paper or provided
(formula sheet, tables, charts). 4. Self-rating 1-5 per chapter (1 = never seen it, 5 = could teach it).
5. "Where does your professor's method or notation differ from the book, and what did they stress in class?"
Record answers verbatim-but-short in course.md. Conventions you discover in slides (a slide method that differs from
the book) go in too, with the slide as source; tell the user which ones you added.

## Given vs must-remember
From past papers: formulas printed inside questions or on a formula page are **given**. Everything a past
solution needs that is not printed is **must remember**. Keep both lists short and per chapter.
