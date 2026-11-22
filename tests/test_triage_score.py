"""Hand-computed triage case (see docs/TRIAGE.md for the formulas).

Papers 2024 (w=1) and 2023 (w=0.7), sum w = 1.7.
  ch  marks 24/23  expected      rating gap   pages cost(20+1.5p)  priority=E*gap/cost*60  needed=cost*(0.4+0.6gap)
  A   10/10        10.000        1      1.0   20    50             12.000                  50.0
  B   20/0         11.765        5      0.2   20    50              2.824                  26.0
  C    0/20         8.235        3      0.6   40    80              3.706                  60.8
  D   20/20        20.000        4      0.4   10    35             13.714                  22.4
Ranking D, A, C, B.
Budget: 3 h/day, now 11-29 08:00, exam 12-01 09:00 -> 2 study days = 360 min;
the mock is shortened to fit the last day: 180 - cram 60 - review 15 = 105;
reserve mock 105 + cram 60 + 15% review 54 = 219 -> budget 141 min.
Greedy: D 22.4 (A, <=84.6), A 72.4 (A), C 133.2 (C: > 0.85*141 = 119.85, <= 141),
B would reach 159.2 > 141 -> X (rated 5/5, so little to gain).
Cut cost = E(B) = 20/1.7 = 11.765.
"""
import json

import pytest

import triage_score as ts
import validate_course_md as v

COURSE = """---
course_code: TT1000
course_name: Triage Test
schema_version: 2
exam_datetime: 2026-12-01T09:00
hours_per_day: 3
book_policy: closed
format: md
paper_total: 50
exam_pattern: |
  Answer all questions.
---

## Book
- path: book.pdf
- page_offset: 0

## Chapters
| id | title | book pages (printed) | lectures | assignments | past papers | self-rating (1-5) |
|----|-------|----|----|----|----|----|
| A | Alpha | 1-20 | - | - | 2024 Q1 (10); 2023 Q1 (10) | 1 |
| B | Beta | 21-40 | - | - | 2024 Q2 (20) | 5 |
| C | Gamma | 41-80 | - | - | 2023 Q2 (20) | 3 |
| D | Delta | 81-90 | - | - | 2024 Q3 (20); 2023 Q3 (20) | 4 |

## Professor conventions (OVERRIDE THE BOOK)
- none

## Given vs must-remember formulas
- none

## Verified corrections log
| date | location | book/slide says | correct value | how verified |
|------|----------|-----------------|---------------|--------------|
"""
NOW = "2026-11-29T08:00"


@pytest.fixture
def course(tmp_path):
    (tmp_path / "book.pdf").write_bytes(b"%PDF-1.4\n")
    p = tmp_path / "course.md"; p.write_text(COURSE)
    return v.load_valid(p)


def by_id(res):
    return {r["id"]: r for r in res["topics"]}


def test_expected_marks_and_priority(course):
    res = ts.score(course, now=NOW)
    t = by_id(res)
    assert t["A"]["expected"] == pytest.approx(10.0)
    assert t["B"]["expected"] == pytest.approx(20 / 1.7)
    assert t["C"]["expected"] == pytest.approx(14 / 1.7)
    assert t["D"]["cost"] == pytest.approx(35)
    assert t["D"]["priority"] == pytest.approx(20 * 0.4 / 35 * 60)
    assert [r["id"] for r in res["topics"]] == ["D", "A", "C", "B"]


def test_budget_tiers_and_cut_cost(course):
    res = ts.score(course, now=NOW)
    assert res["budget"]["available"] == pytest.approx(360)
    assert res["budget"]["for_topics"] == pytest.approx(141)
    tiers = {r["id"]: r["tier"] for r in res["topics"]}
    assert tiers == {"D": "A", "A": "A", "C": "C", "B": "X"}
    assert res["cut_cost"] == pytest.approx(20 / 1.7)
    assert all(r["reason"] for r in res["topics"])


def test_warnings_single_paper_and_totals(course):
    res = ts.score(course, now=NOW)
    w = " ".join(res["warnings"])
    assert "B" in w and "only one paper" in w
    assert "sum" not in w                  # totals are 50 and 50
    course["chapters"][0]["past_papers"][0]["marks"] = 12
    w = " ".join(ts.score(course, now=NOW)["warnings"])
    assert "2024" in w and "52" in w


def test_drill_results_change_ranking(course, tmp_path):
    wm = {"chapters": [{"chapter": "D", "attempts": 8, "accuracy": 1.0, "weakness": 0.0}]}
    res = ts.score(course, now=NOW, weakmap=wm)
    assert [r["id"] for r in res["topics"]][:2] == ["A", "D"]


def test_signals_bonus_and_weights(course):
    sig = {"B": {"slides": 10, "flags": 2, "assignments": 1, "in_pattern": True}}
    base = by_id(ts.score(course, now=NOW))["B"]["expected"]
    boosted = by_id(ts.score(course, now=NOW, signals=sig))["B"]["expected"]
    assert boosted > base
    res = ts.score(course, now=NOW, weights={"recency_decay": 1.0})
    assert by_id(res)["B"]["expected"] == pytest.approx(10.0)


def test_plan_has_review_mock_cram_and_sleep(course):
    res = ts.score(course, now=NOW)
    plan = ts.plan(course, res, now=NOW)
    text = ts.render_plan(plan)
    assert "Mock paper" in text and "Cram" in text and "Sleep" in text
    assert "Spaced review" in text            # day 2 reviews day 1 material
    assert "Beta" not in text                 # tier X is not scheduled
    assert "Gamma" in text
    day_totals = [sum(b["minutes"] for b in d["blocks"]) for d in plan["days"]]
    assert all(t <= 180 + 1e-6 for t in day_totals)


def test_cli_writes_outputs(tmp_path, course):
    out = tmp_path / "sprint"
    code = ts.main([course["path"], "--now", NOW, "--out-dir", str(out)])
    assert code == 0
    assert (out / "triage.md").is_file() and (out / "plan.md").is_file()
    data = json.loads((out / "triage.json").read_text())
    assert data["topics"][0]["id"] == "D"
