# Brief: formula sheet (tunable)

Two outputs: `outputs/formulas.(pdf|md)` (all chosen chapters, two columns) and `outputs/must_remember.(pdf|md)` (one page,
only `\examremember` items; `tmonepage` environment, 3 columns, footnotesize; if it overflows, drop to 4 columns or
\scriptsize; it must stay one page).
Each line: label, the formula, one line "when to use; symbols and units", and the given/remember marker.
Group by question type, not by book section. Include standard values and table entries a student must know
(with the table cited). Conventions from course.md replace the book's version (note "(prof.)").
Dimensional check: for each formula group, at least one claim in recompute.py with units (pint) confirming the
formula is dimensionally consistent with sample values.
