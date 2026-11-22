# Brief: drill (tunable)

## Deck
Per chapter, keep `progress/deck/<id>.json`: a list of items
`{"id": "7-2024Q2b", "kind": "theory|numerical", "type": "oneliner|blank|tf|short|numerical",
  "q": "...", "options": ["...", "..."] or null, "a": "model answer", "source": "book p. 141 / L22 s7 / 2024 Q2b",
  "recipe": "recipe name for numericals", "inputs": {...} or null}`.
Build it lazily the first time a chapter is drilled: past-paper questions first, then assignment and slide problems,
then the book's short-answer questions, then generated items. Theory items: 15-30 per chapter. Numerical items: one
worked example + completion + full problem per recipe. Every model answer is checked against its source (verify
pass) when the deck is built, not during the session.

## Session flow
1. `TM drill_state queue --dir progress [--chapter <id>]` gives due items first. Fill the rest of the session with new
   items (mode `chapter`: that chapter; `weak`: chapters at the top of `progress/weakmap.md`; `mixed`: interleave the
   tier A/B chapters, one item at a time, never two in a row from the same chapter if avoidable).
2. Default 25 minutes or `--minutes N`. Roughly 8-12 theory items or 2-3 numerical loops per 25 minutes.
3. Generated variants of numericals: new input numbers within realistic ranges; compute the answer with
   `recompute.py` **before** asking.
4. Follow the drill-method skill exactly (ask, wait, grade, log).
