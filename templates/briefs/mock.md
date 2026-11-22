# Brief: mock paper (tunable)

1. Pattern: copy the structure from `exam_pattern` and the latest past paper (sections, question count, marks per
   question, choice rules, what formulas are printed in the question, style of one-liners with bracketed options).
2. Marks per chapter follow `sprint/triage.json` expected marks (rounded to the paper's mark units), and include
   at least one question from the student's weakest chapter in `progress/weakmap.md`.
3. **New numbers and new wording.** Never copy past-paper text. Reuse question types, not questions.
4. Answer key with a marking scheme (marks per step). Every key number: claims file + recompute.py; then the
   `verifier` subagent on all key answers (it is a mock, so always). Resolve every MISMATCH before showing anything.
5. Two files: `mock/mock-<n>.(pdf|md)` (questions only, with duration and total) and `mock/mock-<n>-key.(pdf|md)`.
6. Tell the student: set a timer for the stated duration, write answers on paper, then run
   `/tminus:drill` with the key to grade (log each question as a numerical item).
