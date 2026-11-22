---
name: doctor
description: Check that this machine has what tminus needs (Python, PDF text extraction, a TeX engine and LaTeX packages) and print exact per-OS fix commands. Use when the user runs /tminus:doctor or a tminus command reports a missing tool.
argument-hint: "[--install]"
disable-model-invocation: true
allowed-tools: Bash(${CLAUDE_PLUGIN_ROOT}/scripts/tm *), Read, Edit
---

# /tminus:doctor

Run the tminus preflight and help the user fix gaps. Never run `sudo` or a system package manager yourself.

1. Pick the course folder: the current directory if it holds `course.md`, else none.
2. Run, from that folder if there is one:
   `${CLAUDE_PLUGIN_ROOT}/scripts/tm preflight --cache-dir .tminus`
   (without a course folder, drop `--cache-dir .tminus`).
   Show the table to the user as printed. Exit codes: 0 all good, 1 a required item is missing,
   2 usable but optional or PDF-output items are missing.
3. If the arguments contain `--install`, or Python packages are reported missing:
   - Run `${CLAUDE_PLUGIN_ROOT}/scripts/tm preflight --install` (dry run) and show what it will do.
   - Ask the user once to confirm. Only after a yes, run
     `${CLAUDE_PLUGIN_ROOT}/scripts/tm preflight --install --yes`. This installs into the plugin's own
     virtualenv (`~/.cache/tminus/venv`, or `$TMINUS_VENV`), never globally.
   - Re-run step 2.
4. For system-level gaps (TeX, poppler, Python itself), show the printed fix command and ask the user to run it
   themselves (they can type `! <command>` in the prompt). Do not run it for them.
5. Output format: if `recommended format` is `md` and `course.md` exists, ask whether to set `format: md`
   (works with no LaTeX; every command then writes Markdown). If yes, edit the front matter. If the user later
   installs TeX, they can switch back to `format: pdf`.
6. Finish with one line: ready / ready in Markdown mode / blocked on <item>.
