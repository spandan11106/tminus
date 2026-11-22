# Decisions and deviations from PLAN.md

| # | Date | Decision | Reason |
|---|---|---|---|
| 1 | 2026-11-22 | User-facing commands are written as **skills** (`skills/<cmd>/SKILL.md`, `disable-model-invocation: true`) instead of `commands/*.md`. Internal skills (course-context, verify-pass, figure-handling, drill-method) use `user-invocable: false`. | Current docs (code.claude.com/docs/en/plugins/components) say `commands/` is the legacy format and new commands should be skills. Invocation is unchanged: `skills/triage/SKILL.md` is `/tminus:triage`. PLAN rule 10: trust current docs. |
| 2 | 2026-11-22 | Scripts are called as `${CLAUDE_PLUGIN_ROOT}/scripts/tm <script> ...`; `tm` is a bash wrapper that picks the plugin venv Python if present, else `python3`. | `${CLAUDE_PLUGIN_ROOT}` is substituted inline in skill Markdown but is not exported to Bash-tool commands; a wrapper keeps venv selection in one place. |
| 3 | 2026-11-22 | Plugin venv default `~/.cache/tminus/venv`, override with `TMINUS_VENV`. | As in PLAN 5.0. `${CLAUDE_PLUGIN_DATA}` was considered but is not available to plain Bash calls. |
| 4 | 2026-11-22 | pymupdf pinned to 2.1 (current, tested) rather than 1.x. | It is the version installed and tested in the build venv. |
