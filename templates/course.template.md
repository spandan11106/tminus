---
course_code: XX0000
course_name: Course Name
schema_version: 2
exam_datetime: 2026-01-01T09:00     # local time; used to compute hours left
hours_per_day: 6                    # study hours available per day
book_policy: closed                 # closed | open | formula-sheet-allowed
format: pdf                         # pdf | md   (doctor sets md if no TeX engine)
exam_pattern: |
  Describe the paper: sections, marks, choice ("any 5 of 7"), what is printed on the paper.
paper_total: 50                     # marks in one paper; triage checks past papers sum to this
papers:                             # optional, per past paper: year, weight (overrides recency), total, partial
  2024: {year: 2024}
  # Mid24: {year: 2024, weight: 0.5, partial: true}   # midsem / quiz / partly out-of-scope paper
---

## Book
- path: book.pdf
- page_offset: 0                    # pdf_page = printed_page + page_offset

## Chapters
| id | title | book pages (printed) | lectures | assignments | past papers | self-rating (1-5) |
|----|-------|----------------------|----------|-------------|-------------|--------------------|
| 1 | First chapter | 1-20 | L01, L02 | A1 | 2024 Q2 (10) | 3 |

<!-- past papers cell: "<year> <question> (<marks>)", several separated by ";" -->

## Professor conventions (OVERRIDE THE BOOK)
<!-- One bullet each: topic | what the professor does | source | date added -->
- (none yet)

## Given vs must-remember formulas
### Given in the paper
- (none yet)
### Must remember
- (none yet)

## Verified corrections log
| date | location | book/slide says | correct value | how verified |
|------|----------|-----------------|---------------|--------------|
