"""Scripted part of Gate 5 on the toy course: triage ranking (hand-computed), drill -> weakmap -> re-triage.

Hand computation (no signals file; emphasis = lectures + assignments listed in course.md):
  papers 2024 (w 1), 2023 (w 0.7); E_base = (m24 + 0.7 m23) / 1.7
    ch1 12.6/1.7 = 7.412   ch2 25.2/1.7 = 14.824   ch3 27.8/1.7 = 16.353   ch4 19.4/1.7 = 11.412
  mean = 50/4 = 12.5; emphasis raw 2, 3, 2, 2 (max 3); bonus = 12.5 * 0.15 * raw/3
    E: ch1 8.662  ch2 16.699  ch3 17.603  ch4 12.662
  cost = max(30, 20 + 1.5 * pages) = 30 for all (5-6 pages each)
  gap (ratings 2, 4, 3, 1) = 0.8, 0.4, 0.6, 1.0; priority = E * gap * 2
    ch1 13.86  ch2 13.36  ch3 21.12  ch4 25.32  -> ranking 4, 3, 1, 2
After 6 wrong drill attempts on ch2: gap = 0.4*0.4 + 0.6*1.0 = 0.76 -> priority 25.38 > ch4 25.32 -> ch2 first.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

import drill_state as ds
import triage_score as ts
import validate_course_md as v

ROOT = Path(__file__).resolve().parents[1]
NOW = "2026-11-28T09:00"


@pytest.fixture(scope="module")
def toy(tmp_path_factory):
    out = tmp_path_factory.mktemp("toy")
    subprocess.run([sys.executable, str(ROOT / "tests/fixtures/make_toycourse.py"), str(out)],
                   check=True, capture_output=True)
    (out / "course.md").write_text((out / "course.expected.md").read_text())
    return out


def test_toy_triage_ranking(toy):
    c = v.load_valid(toy / "course.md")
    res = ts.score(c, now=NOW)
    assert [t["id"] for t in res["topics"]] == ["4", "3", "1", "2"]
    E = {t["id"]: t["expected"] for t in res["topics"]}
    assert E["3"] == pytest.approx(27.8 / 1.7 + 1.25, abs=1e-3)
    assert all(t["tier"] == "A" for t in res["topics"])
    assert any("Chapter 1" in w and "only one paper" in w for w in res["warnings"])
    assert not any("sum to" in w for w in res["warnings"])


def test_toy_drill_changes_triage(toy):
    prog = toy / "progress"
    for i in range(6):
        ds.log_attempt(prog, {"chapter": "2", "item": f"2-gen-{i}", "kind": "numerical",
                              "result": "wrong", "note": "used degrees in torsion formula"}, now=NOW)
    wm = ds.rebuild(prog)
    assert wm["chapters"][0]["chapter"] == "2"
    assert ds.queue(prog, now=NOW)            # wrong items are due again
    code = ts.main([str(toy / "course.md"), "--now", NOW])
    assert code == 0
    data = json.loads((toy / "sprint" / "triage.json").read_text())
    assert data["topics"][0]["id"] == "2"
    assert "drill accuracy 0%" in data["topics"][0]["reason"]
    assert "used degrees" in (prog / "errors.md").read_text()
