# How triage ranks topics

`scripts/triage_score.py` is deterministic and unit-tested (`tests/test_triage_score.py` has a hand-computed
case). Every weight is in `DEFAULT_WEIGHTS` and can be overridden per course in `sprint/weights.json`.
Rankings are heuristics, not predictions: there are no pass odds anywhere.

## Expected marks E
- Papers are ordered newest first; paper *i* gets weight `recency_decay^i` (default 0.7).
- `base = sum(w_p * marks_p) / sum(w_p)` over **all** papers (a chapter missing from a paper scores 0 there),
  so it is the recency-weighted average marks per paper.
- `bonus = mean_chapter_marks * (0.15 * emphasis + 0.10 * in_pattern)`, where
  `emphasis = (slides + 2 * flags + assignments) / max over chapters`. Without a signals file, slides =
  number of lectures listed and assignments = number of assignments listed in `course.md`. Flags are
  "important" / "exam" marks the professor put on slides (found by `/tminus:setup`).
- `E = base + bonus`.

## Study cost and gap
- `cost = clamp(20 + pages * minutes_per_page, 30, 240)` minutes; minutes per page 1.0 theory, 2.0 numerical,
  1.5 mixed (default).
- `gap = (6 - self_rating) / 5` (rating 1 -> 1.0, rating 5 -> 0.2). Once a chapter has at least 5 drill
  attempts: `gap = 0.4 * self_gap + 0.6 * (1 - recent drill accuracy)`.
- `priority = E * gap / cost * 60` (marks-gap per hour). Higher is better.
- `needed = cost * (0.4 + 0.6 * gap)` minutes.

## Budget, tiers and cut line
- Study minutes: `hours_per_day` for each day before the exam day; today counts only until 23:00.
- Reserve: the mock (120 min, shortened to fit the last day, moved a day earlier if under 60), the cram
  pack (60 min) and 15 % for spaced review. The rest is the topic budget.
- Topics are taken in priority order. One that does not fit is tier X; the next ones may still fit.
  Tier A while cumulative minutes <= 60 % of the budget (the top topic is always A), B <= 85 %, C <= 100 %.
- The cut cost is the sum of E over tier X: expected marks per paper given up, on past-paper averages.

## Warnings
- Tagged marks per paper do not sum to `paper_total`.
- A chapter appears in only one paper (it may be a one-off).
- A choice-based paper ("any 5 of 7") needs less than full coverage.

## Limits
Past papers are a small sample; syllabus changes and new examiners break the pattern. Read the per-topic
reason and edit the weights or your ratings if they do not match what you know.
