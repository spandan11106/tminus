---
name: mock
description: "Generate a timed mock paper in the examiner's style with new numbers, plus an answer key and marking scheme where every number is recomputed and independently verified."
argument-hint: "[--minutes N]"
disable-model-invocation: true
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/tm *)
---

# /tminus:mock $ARGUMENTS

Let `TM` be `${CLAUDE_PLUGIN_ROOT}/scripts/tm`.
1. Follow the course-context skill. Needs `sprint/triage.json` (run /tminus:triage first if missing).
2. Follow `${CLAUDE_PLUGIN_ROOT}/templates/briefs/mock.md`. Duration: `--minutes` or the real paper's duration.
3. Verify pass in full, **and** run the `verifier` subagent on every answer-key claim (parse its output with
   `TM agent_output verifier .tminus/verifier-mock-<n>.json`, a file the agent writes itself). Do not show the paper until every key answer is OK or fixed.
4. Build both files. Give the student the paper path and the timer length only. Do not print the key's path or
   any answer; reveal the key only when the student says they have finished.
5. Offer: "When done, run /tminus:drill and paste your answers to grade them."
