# Build environment (Phase 0, Layer A)

Checked 2026-11-22 on the build machine.

| Tool | Status | Version / path | Notes |
|---|---|---|---|
| OS | OK | Arch Linux (rolling), kernel 7.2 | |
| python3 >= 3.9 | OK | 3.14.10 | system Python is externally managed; never pip install into it |
| git | OK | /usr/bin/git | |
| pip + venv module | OK | | project venv at `.venv/` |
| latexmk + pdflatex | OK | texlive-binextra / texlive-bin 2026 | |
| tectonic | MISSING | | optional fallback; not installed (latexmk present, so not needed) |
| pdftoppm / pdftotext | OK | poppler 26.10 | |
| PyMuPDF | OK (venv) | 2.1 | |
| kpsewhich | OK | texlive-bin | used to test LaTeX packages |
| network (docs site) | OK | code.claude.com reachable | plugin docs fetched 2026-11-22 |
| free disk | OK | 288 GB free on /home | |
| claude CLI | OK | 2.1.322 | `claude plugin validate`, `claude --plugin-dir` |

Python dependencies (venv): see `requirements.txt` (pymupdf, PyYAML, Pint, pytest, reportlab).

No system installs were needed, so no sudo was run. All PDF gates can run on this machine.
