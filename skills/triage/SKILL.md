---
name: triage
description: "Rank chapters by expected marks per study minute for the time left, set the cut line, and write a day-by-day sprint plan with spaced review, a timed mock and the cram block. Re-run daily: it reads drill results and re-plans."
disable-model-invocation: true
---

# /tminus:triage

Let `TM` be `${CLAUDE_PLUGIN_ROOT}/scripts/tm`.
1. Follow the course-context skill (preflight, validate course.md, load conventions).
2. Follow `${CLAUDE_PLUGIN_ROOT}/templates/briefs/triage.md`. The scoring is done by `TM triage_score`, never by
   hand: its formulas are in `${CLAUDE_PLUGIN_ROOT}/docs/TRIAGE.md`; explain them if asked.
3. If `progress/weakmap.json` exists, say that drill results were used.
4. End with today's first block as a command to run (e.g. `/tminus:pack 7`).
