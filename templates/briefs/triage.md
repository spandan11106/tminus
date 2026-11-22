# Brief: triage (tunable)

1. Make sure `sprint/signals.json` exists (setup writes it). If missing, build it: count slides per chapter, flags
   (important/exam markers), assignments per chapter; set `in_pattern` for topics named in `exam_pattern`; `kind`
   numerical if past questions for the chapter are mostly numericals.
2. Run `TM triage_score course.md --signals sprint/signals.json` (it also reads `progress/weakmap.json` and
   `sprint/weights.json` when present). It writes `sprint/triage.md`, `sprint/plan.md`, `sprint/triage.json`.
3. Show the user: the ranked table, the cut line and what it costs, the warnings, and today's blocks from the plan.
   Keep it short. Do not restate the whole plan.
4. On a re-run (a previous `sprint/triage.json` exists), compare and say what moved and why in at most 5 lines
   (e.g. "Ch 7 up: drill accuracy 40 % on bolted joints").
5. If the user disagrees with a ranking, change `sprint/weights.json` or the self-rating in course.md (ask which)
   and re-run. Never hand-edit the outputs.
6. Language: rankings are heuristics. No percentages of passing, no predicted scores.
