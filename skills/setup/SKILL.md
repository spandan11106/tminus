---
name: setup
description: "Ingest a course folder (book, slides, assignments, past papers) and write course.md: page offset, chapter map, past-paper marks, professor conventions, given vs must-remember formulas. Use --refresh after new lectures arrive."
argument-hint: "[--refresh]"
disable-model-invocation: true
---

# /tminus:setup

Let `TM` be `${CLAUDE_PLUGIN_ROOT}/scripts/tm`. Read `${CLAUDE_PLUGIN_ROOT}/templates/briefs/setup.md` first and
follow it. Work in the current folder (the course folder). Never copy course files into the plugin.

1. Run `TM preflight --cache-dir .tminus`. If the recommended format is `md`, note it for step 7.
2. **Inventory** (brief: classification, scanned-PDF check). Show a compact table: file, class, pages, confidence.
   List unclassified and image-only files and say what is needed.
3. **Page offset** from three body pages (brief). Show the pages used.
4. **Chapters, mapping, marks** (brief). Check each paper's tagged marks sum to its total.
5. **[ASK USER]** one batch with AskUserQuestion or a short numbered list: exam date/time, hours per day, book
   policy and what is printed, self-rating 1-5 per examinable chapter, and the professor-vs-book question.
   Show any convention you found in the slides and ask the user to confirm it.
6. Draft the given-vs-must-remember lists from the past papers. Book or slide errors you found go to
   `progress/corrections_candidates.md` with how you verified them; move a row into course.md's corrections log
   only after the user confirms it (include them in the step-5 batch when you already know them).
7. Write `course.md` from `${CLAUDE_PLUGIN_ROOT}/templates/course.template.md` (format `pdf` or `md`), plus
   `sprint/signals.json`. Run `TM validate_course_md course.md` and fix until it passes.
8. Finish with: the low-confidence mappings only, the conventions recorded, and "next: /tminus:triage".

## --refresh
Re-inventory; for new or changed lectures, slides and papers: update mappings, signals and conventions. Then list
**every answer, recipe or formula in existing `packs/`, `progress/deck/` and `mock/` that changes** because of a new
convention, with file and old/new value, and offer to regenerate those packs. Re-run the validator.
