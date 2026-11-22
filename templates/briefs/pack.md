# Brief: chapter pack (tunable)

Target: the student can do this chapter's exam questions after **30-45 minutes** with the pack plus a drill.
Not a textbook. Length: 3-6 pages (PDF) for a typical chapter.

Fixed structure (templates/pack.tex or pack.md.tmpl):
1. **60-second snapshot**: 4-6 bullets. What was asked (paper, question, marks), which question types repeat,
   what the professor stresses. From `sprint/triage.json` and the past papers.
2. **Recipes**: one per numerical question type, numbered steps in the **professor's method** (conventions win).
   Each step names the formula and the decision to make (which case, which end of a range, which convention).
3. **Worked examples**: 2-4. Order: past-paper question (full solution, exam style) > professor's slide example >
   assignment problem > book example. Every number goes through the verify pass. State the source of each.
   Where the book's answer differs because of a convention, show the professor's answer and say why in one line.
4. **Formulas**: only this chapter's; units on every symbol; `\examgiven` or `\examremember` on each line.
5. **Common traps**: from the corrections log, `progress/errors.md` (the student's own repeated mistakes, first),
   conventions that differ from the book, unit slips, reversed limits.
6. **Drill pointer**: `/tminus:drill <id>`.
7. **Verification report**.

No long theory prose: definitions and one-liners go into the drill deck instead
(`progress/deck/<id>.json`, see the drill brief). Figures only where a question needs them (figure rule).
Output: `packs/<id>.tex` -> `packs/<id>.pdf` via `TM build_doc packs/<id>.tex` (or `packs/<id>.md`).
