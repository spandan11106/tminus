---
name: pack
description: "Build a compact, verified chapter pack (60-second snapshot, recipes in the professor's method, 2-4 worked examples, formulas with given/remember markers, common traps) sized to 30-45 minutes. Argument: a chapter id, several ids, or tier-A."
argument-hint: "<chapter id ... | tier-A>"
disable-model-invocation: true
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/tm *)
---

# /tminus:pack $ARGUMENTS

Let `TM` be `${CLAUDE_PLUGIN_ROOT}/scripts/tm`.
1. Follow the course-context skill.
2. Resolve the chapters: ids from `$ARGUMENTS`, or `tier-A` = tier A in `sprint/triage.json` (run /tminus:triage first
   if it is missing). Generate only these. Tell the user the scope before starting if it is more than 2 chapters.
3. For each chapter, read `${CLAUDE_PLUGIN_ROOT}/templates/briefs/pack.md` and the sources: the book pages for the
   chapter (`pdftotext` with the offset), the mapped lectures, assignments and past-paper questions, the corrections
   log, `progress/errors.md`. With more than 2 chapters, you may hand each chapter to a subagent with this brief;
   each must follow the course-context, figure-handling and verify-pass rules.
4. Write `packs/<id>.tex` from `${CLAUDE_PLUGIN_ROOT}/templates/pack.tex` (format pdf) or `packs/<id>.md` from
   `pack.md.tmpl` (format md). Use only `tminus.sty` macros; ASCII only in .tex.
5. Seed the drill deck `progress/deck/<id>.json` with the chapter's one-liners and question items (drill brief).
6. Follow the verify-pass skill (claims file, recompute, source checks, report at the end of the pack).
7. Build: `TM build_doc packs/<id>.tex` (or `.md`). Fix gate failures (ASCII, overfull, placeholders) and rebuild.
   Then render pages at low resolution into `.tminus/` (`pdftoppm -r 50 -png packs/<id>.pdf .tminus/<id>`), view
   them, and fix anything that looks wrong (clipped boxes, broken math, empty pages).
8. Report: output path, pages, study minutes, flags raised, and "next: /tminus:drill <id>".
