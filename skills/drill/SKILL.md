---
name: drill
description: "Interactive active-recall session: question-first retrieval for theory, worked-example then completion then full problem for numericals, graded against the professor's conventions, logged to progress/. Modes: a chapter id, weak, or mixed."
argument-hint: "[<chapter id> | weak | mixed] [--minutes N]"
disable-model-invocation: true
---

# /tminus:drill $ARGUMENTS

Let `TM` be `${CLAUDE_PLUGIN_ROOT}/scripts/tm`.
1. Follow the course-context skill.
2. Read `${CLAUDE_PLUGIN_ROOT}/templates/briefs/drill.md` and follow the drill-method skill **exactly**.
3. Mode from `$ARGUMENTS` (default: `mixed` if tier A has more than one chapter, else that chapter); minutes from
   `--minutes` (default 25). Say the mode and length in one line, then ask the first question.
4. Build the chapter's deck first if `progress/deck/<id>.json` does not exist (verify its answers before the session).
5. One item per message. Wait for the answer. Grade, give the model answer briefly, log with `TM drill_state log`.
6. If the student pastes a full solution to check (their own work or a mock answer), grade method first against the
   conventions, then numbers with recompute.py, and log it as a numerical item.
7. At the end: `TM drill_state rebuild --dir progress`, the three-line summary, and the next session suggestion.
