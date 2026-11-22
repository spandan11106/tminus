---
name: formulas
description: "Build the two-column formula sheet across chosen chapters (formula, when to use, units, given/remember marker) and a one-page must-remember sheet, with dimensional checks."
argument-hint: "[chapter ids | all]"
disable-model-invocation: true
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/tm *)
---

# /tminus:formulas $ARGUMENTS

Let `TM` be `${CLAUDE_PLUGIN_ROOT}/scripts/tm`.
1. Follow the course-context skill. Chapters: `$ARGUMENTS`, default all tier A-C chapters from `sprint/triage.json`
   (all chapters if triage has not run).
2. Follow `${CLAUDE_PLUGIN_ROOT}/templates/briefs/formulas.md`. Reuse formulas already verified in `packs/` where they
   exist; take the rest from the book pages and slides (read them; do not write formulas from memory).
3. Use `tmsheet` / `tmformula` / `tmfsection` and `tmonepage` from tminus.sty (Markdown: tables).
4. Verify pass, including the dimensional checks. Build both files with `TM build_doc`; the must-remember sheet must
   be exactly one page (check the page count build_doc prints).
