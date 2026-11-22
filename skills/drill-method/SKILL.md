---
name: drill-method
description: "Rules for running tminus drill sessions: question-first retrieval for theory, and the worked-example then completion then full-problem loop for numericals, with grading against the professor's conventions. Use inside /tminus:drill and when grading answers."
user-invocable: false
---

# Drill method

Theory and procedures are drilled differently. Retrieval practice works for facts; for problem-solving,
worked examples followed by practice work better than blind quizzing on an unseen procedure.

## Theory and facts: retrieval
1. Ask **one** question and **stop**. Wait for the student's answer. Never show the answer in the same message.
2. Grade: `correct`, `partial`, `hesitant` (right but unsure or slow; ask "how sure were you?" if unclear) or `wrong`.
   Compare with the book or slide text; the professor's wording wins. Give the model answer in one or two lines.
3. Types: one-liners with bracketed options (the examiner's style), fill in the blank, true or false, short answer.
4. Wrong or hesitant items come back later in the same session (after at least 3 other items) and the next day.

## Numericals: worked-example loop
For each recipe (question type):
1. **Worked example**: show a short, complete solution in the professor's method.
2. **Completion problem**: the same type with new numbers and the first steps done; the student does the rest.
3. **Full problem**: new numbers, nothing done.
Feedback order: **method first** (right formula, right convention, right units), then numbers. Check the student's
numbers with `recompute.py`. Hints only on request. Never reveal the answer before an attempt unless the student
types `skip`. A student who already solved full problems of a type correctly can skip straight to step 3.

## Logging
After every graded item run
`${CLAUDE_PLUGIN_ROOT}/scripts/tm drill_state log --dir progress --chapter <id> --item <stable-id> --kind theory|numerical --result <r> [--note "<the mistake, in a few words>"] [--source "<paper/assignment/slide>"]`.
Notes must name the mistake so they group well ("used book stiffness ratio, not stress area"; "forgot Wahl factor").
Item ids are stable across sessions: `<chapter>-<source>-<n>` (for example `7-2024Q2b`, `10-gen-3`).

## Sessions
Timeboxed. No points, streaks or praise padding. End with exactly three lines: what went well, what to fix,
the suggested next session (command and minutes). Then run `drill_state rebuild --dir progress`.
