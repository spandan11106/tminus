---
course_code: ME0000
course_name: Example Machine Design
schema_version: 2
exam_datetime: 2026-12-01T09:30     # local time; used to compute hours left
hours_per_day: 6                    # study hours available per day
book_policy: closed                 # closed | open | formula-sheet-allowed
format: pdf                         # pdf | md   (doctor sets md if no TeX engine)
exam_pattern: |
  Q1: twenty one-liners with bracketed options (1 mark each). Q2-Q6: numericals; key formulas printed in the question.
paper_total: 50                     # marks in one paper; triage checks past papers sum to this
---

## Book
- path: book/textbook.pdf
- page_offset: 24                   # pdf_page = printed_page + page_offset

## Chapters
| id | title | book pages (printed) | lectures | assignments | past papers | self-rating (1-5) |
|----|-------|----------------------|----------|-------------|-------------|--------------------|
| 5 | Fluctuating loads | 141-183 | L35, L36 | A4 | 2024 Q2a (8); 2024 Q1(xiv) (1) | 2 |
| 7 | Threaded joints | 219-271 | L22, L23 | A5 | 2024 Q2b (10); 2024 Q1(iii) (1) | 3 |
| 10 | Springs | 393-447 | L37, L38 | A7 | 2024 Q5 (10); 2024 Q6 (9) | 1 |

<!-- past papers cell: "<year> <question> (<marks>)", several separated by ";" -->

## Professor conventions (OVERRIDE THE BOOK)
<!-- One bullet each: topic | what the professor does | source | date added -->
- Bolt joint stiffness | ratio by bolt stress area, C = At/(At+Ap), not by modulus | L22 slide 7 | 2026-11-20
- Fatigue | Kf applied to both mean and alternating stress | L38 | 2026-11-20

## Given vs must-remember formulas
### Given in the paper
- Spring shear stress and deflection, Wahl factor (2024 Q5)
### Must remember
- Goodman line; free length = solid length + deflection + 15 % clash allowance

## Verified corrections log
| date | location | book/slide says | correct value | how verified |
|------|----------|-----------------|---------------|--------------|
| 2026-11-20 | Example 12.14, printed p. 480 | temperature rise 73 C | 7.3 C | recompute.py |
