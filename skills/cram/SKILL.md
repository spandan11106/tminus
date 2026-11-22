---
name: cram
description: "Night-before pack: one page of must-remember formulas, one page of one-liners ordered by exam likelihood and your weak items, top repeated mistakes, last paper solved, exam-day checklist. No new material."
disable-model-invocation: true
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/tm *)
---

# /tminus:cram

Let `TM` be `${CLAUDE_PLUGIN_ROOT}/scripts/tm`.
1. Follow the course-context skill.
2. Follow `${CLAUDE_PLUGIN_ROOT}/templates/briefs/cram.md` using `${CLAUDE_PLUGIN_ROOT}/templates/cram.tex` (or a
   Markdown equivalent). Pull only from existing packs, the deck, the formula sheet, `progress/errors.md`, the
   corrections log and past papers.
3. Full verify pass. Build with `TM build_doc`. Pages 1 and 2 must be one page each.
4. Close with one line: sleep reminder and what to skim in the morning (20-30 min).
