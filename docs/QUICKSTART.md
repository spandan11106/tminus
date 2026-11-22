# Quick start

## 1. Get the plugin
Either install from the marketplace in this repo:
```
/plugin marketplace add <owner>/tminus        # or a local path to this folder
/plugin install tminus@tminus-marketplace
```
or load it straight from a clone for one session:
```
git clone <repo-url> ~/tminus
claude --plugin-dir ~/tminus
```
Check it loaded: `claude --plugin-dir ~/tminus plugin details tminus` lists the skills.

## 2. Three steps
1. `/tminus:doctor` checks Python, PDF tools and LaTeX, and prints the exact fix command for your OS.
   No LaTeX? Say yes to Markdown mode and carry on.
2. `cd` into a folder holding your course files (book PDF, slides, assignments, past papers), then
   `/tminus:setup`. Answer one short batch of questions (exam time, hours per day, self-ratings,
   what your professor does differently from the book).
3. `/tminus:triage` gives the ranked topic list, the cut line, and a day-by-day plan.

Then follow the plan: `/tminus:pack <chapter>`, `/tminus:drill`, `/tminus:mock`, and `/tminus:cram` the night before.

## Developing
```
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
scripts/selftest.sh                       # unit tests, preflight simulation, template builds
claude plugin validate .
```
