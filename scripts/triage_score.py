#!/usr/bin/env python3
"""Transparent, deterministic triage scoring and day-by-day plan. Formulas: docs/TRIAGE.md.

CLI: triage_score.py course.md [--now ISO] [--signals F.json] [--weakmap F.json]
                     [--weights F.json] [--out-dir DIR] [--json]
Writes DIR/triage.md, DIR/plan.md, DIR/triage.json (default DIR: <course dir>/sprint).
Rankings are heuristics. No pass odds, no percentages of success.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_course_md import load_valid  # noqa: E402

DEFAULT_WEIGHTS = {
    "recency_decay": 0.7,        # weight of each older paper relative to the next newer one
    "emphasis_bonus": 0.15,      # x mean chapter marks x normalised lecture emphasis
    "pattern_bonus": 0.10,       # x mean chapter marks if the topic is in the stated exam pattern
    "minutes_per_page": {"theory": 1.0, "numerical": 2.0, "mixed": 1.5},
    "base_minutes": 20, "min_cost": 30, "max_cost": 240, "default_pages": 15,
    "drill_weight": 0.6,         # share of the gap taken from drill accuracy once enough attempts
    "drill_min_attempts": 5,
    "tier_A": 0.60, "tier_B": 0.85,   # cumulative share of the topic budget
    "review_share": 0.15, "mock_minutes": 120, "mock_min_minutes": 60, "cram_minutes": 60,
    "pack_share": 0.35,          # share of a topic's minutes spent on its pack; the rest is drill
    "day_end_hour": 23,
}


def _dt(x) -> dt.datetime:
    if isinstance(x, dt.datetime):
        return x
    if isinstance(x, dt.date):
        return dt.datetime.combine(x, dt.time(9, 0))
    return dt.datetime.fromisoformat(str(x))


def _weights(over: dict | None) -> dict:
    w = json.loads(json.dumps(DEFAULT_WEIGHTS))
    for k, val in (over or {}).items():
        if isinstance(val, dict) and isinstance(w.get(k), dict):
            w[k].update(val)
        else:
            w[k] = val
    return w


def study_days(course: dict, now, w: dict) -> list[dict]:
    """Calendar days from now until the exam day (exclusive) with their study minutes."""
    now, exam = _dt(now), _dt(course["front"]["exam_datetime"])
    cap = float(course["front"]["hours_per_day"]) * 60
    days, d = [], now.date()
    while d < exam.date():
        if d == now.date():
            end = dt.datetime.combine(d, dt.time(w["day_end_hour"], 0))
            m = min(cap, max(0.0, (end - now).total_seconds() / 60))
        else:
            m = cap
        if m > 0:
            days.append({"date": d.isoformat(), "minutes": m})
        d += dt.timedelta(days=1)
    return days


LAST_DAY_REVIEW = 15


def mock_slot(days: list[dict], w: dict):
    """(minutes, on_last_day): the mock is the last block before the cram on the final day,
    shortened to fit; if even mock_min_minutes does not fit it moves to the day before."""
    if not days:
        return 0, True
    room = days[-1]["minutes"] - w["cram_minutes"] - LAST_DAY_REVIEW
    m = min(w["mock_minutes"], max(0, room))
    if m >= w["mock_min_minutes"] or len(days) == 1:
        return max(m, 0), True
    return min(w["mock_minutes"], days[-2]["minutes"]), False


def score(course: dict, now=None, signals=None, weakmap=None, weights=None) -> dict:
    w = _weights(weights)
    now = _dt(now or dt.datetime.now().replace(second=0, microsecond=0))
    signals = signals or {}
    chapters = course["chapters"]
    papers = sorted({p["paper"] for ch in chapters for p in ch["past_papers"]}, reverse=True)
    pw = {p: w["recency_decay"] ** i for i, p in enumerate(papers)}
    sum_w = sum(pw.values()) or 1.0

    # emphasis signals (defaults from course.md lecture/assignment counts)
    def sig(ch):
        s = signals.get(ch["id"], {})
        return {"slides": s.get("slides", len(ch["lectures"])), "flags": s.get("flags", 0),
                "assignments": s.get("assignments", len(ch["assignments"])),
                "in_pattern": bool(s.get("in_pattern", False)), "kind": s.get("kind", "mixed")}
    sigs = {ch["id"]: sig(ch) for ch in chapters}
    raw_emph = {k: s["slides"] + 2 * s["flags"] + s["assignments"] for k, s in sigs.items()}
    max_emph = max(raw_emph.values()) if raw_emph else 0

    base_exp = {}
    for ch in chapters:
        by_paper = {}
        for p in ch["past_papers"]:
            by_paper[p["paper"]] = by_paper.get(p["paper"], 0) + p["marks"]
        base_exp[ch["id"]] = (sum(pw[p] * m for p, m in by_paper.items()) / sum_w, by_paper)
    mean_marks = sum(e for e, _ in base_exp.values()) / max(len(chapters), 1)

    drill = {c["chapter"]: c for c in (weakmap or {}).get("chapters", [])}
    topics = []
    for ch in chapters:
        cid, s = ch["id"], sigs[ch["id"]]
        exp, by_paper = base_exp[cid]
        emph = raw_emph[cid] / max_emph if max_emph else 0.0
        bonus = mean_marks * (w["emphasis_bonus"] * emph + w["pattern_bonus"] * s["in_pattern"])
        E = exp + bonus
        pages = (ch["pages"][1] - ch["pages"][0] + 1) if ch["pages"] else w["default_pages"]
        mpp = w["minutes_per_page"].get(s["kind"], w["minutes_per_page"]["mixed"])
        cost = min(max(w["base_minutes"] + pages * mpp, w["min_cost"]), w["max_cost"])
        self_gap = (6 - ch["self_rating"]) / 5
        d = drill.get(cid)
        if d and d.get("attempts", 0) >= w["drill_min_attempts"]:
            gap = (1 - w["drill_weight"]) * self_gap + w["drill_weight"] * d["weakness"]
            gap_src = f"rated {ch['self_rating']}/5, drill accuracy {d['accuracy']:.0%}"
        else:
            gap = self_gap
            gap_src = f"rated {ch['self_rating']}/5"
        priority = E * gap / cost * 60
        needed = cost * (0.4 + 0.6 * gap)
        papers_txt = ", ".join(f"{p}: {m:g}" for p, m in sorted(by_paper.items(), reverse=True)) or "not in past papers"
        reason = (f"{E:.1f} expected marks ({papers_txt}"
                  f"{'; +emphasis' if bonus > 0 else ''}); {gap_src}; ~{needed:.0f} min; "
                  f"{priority:.2f} marks-gap per hour")
        topics.append({"id": cid, "title": ch["title"], "expected": E, "expected_base": exp,
                       "bonus": bonus, "by_paper": by_paper, "pages": pages, "cost": cost,
                       "gap": gap, "priority": priority, "needed": needed, "reason": reason})
    topics.sort(key=lambda t: (-t["priority"], -t["expected"], t["id"]))

    days = study_days(course, now, w)
    available = sum(d["minutes"] for d in days)
    mock_m, _ = mock_slot(days, w)
    reserve = mock_m + w["cram_minutes"] + w["review_share"] * available
    budget = max(0.0, available - reserve)
    cum = 0.0
    for i, t in enumerate(topics):
        if cum + t["needed"] <= budget or (i == 0 and budget > 0):
            cum += t["needed"]
            t["cumulative"] = cum
            t["tier"] = "A" if cum <= w["tier_A"] * budget or i == 0 else (
                "B" if cum <= w["tier_B"] * budget else "C")
        else:
            t["cumulative"] = None
            t["tier"] = "X"
    cut_cost = sum(t["expected"] for t in topics if t["tier"] == "X")

    warnings = []
    total = course["front"].get("paper_total")
    for p in papers:
        s = sum(m for ch in chapters for pp in ch["past_papers"] if pp["paper"] == p for m in [pp["marks"]])
        if total and abs(s - total) > 1e-9:
            warnings.append(f"Paper {p}: tagged marks sum to {s:g}, not the paper total {total:g}. "
                            "Some questions are untagged or double-counted in course.md.")
    if len(papers) >= 2:
        for t in topics:
            if len(t["by_paper"]) == 1:
                warnings.append(f"Chapter {t['id']} ({t['title']}) appears in only one paper "
                                f"({next(iter(t['by_paper']))}); it may be a one-off.")
    pattern = str(course["front"].get("exam_pattern", "")).lower()
    if "any " in pattern or "choice" in pattern:
        warnings.append("The paper has a choice of questions: you need less than full coverage, "
                        "so skipping tier X costs less than the number above suggests.")
    if not papers:
        warnings.append("No past-paper marks in course.md: ranking uses only emphasis and self-ratings.")
    if budget <= 0:
        warnings.append("No time left for new topics after mock, cram and review: drill tier A only.")
    return {"now": now.isoformat(), "papers": papers, "paper_weights": pw, "weights": w,
            "budget": {"available": available, "reserve": reserve, "for_topics": budget},
            "topics": topics, "cut_cost": cut_cost, "warnings": warnings, "days": days}


def plan(course: dict, res: dict, now=None) -> dict:
    w = res["weights"]
    days = [dict(d, blocks=[], free=d["minutes"]) for d in res["days"]]
    if not days:
        return {"days": [], "exam": str(course["front"]["exam_datetime"])}

    def add(day, kind, label, minutes):
        minutes = round(min(minutes, day["free"]))
        if minutes > 0:
            day["blocks"].append({"kind": kind, "label": label, "minutes": minutes})
            day["free"] -= minutes
        return minutes

    last = days[-1]
    mock_m, on_last = mock_slot(res["days"], w)
    tail = [("cram", "Cram pack: formulas page, one-liners, top mistakes (/tminus:cram)", w["cram_minutes"])]
    if on_last and mock_m > 0:
        short = " (shortened)" if mock_m < w["mock_minutes"] else ""
        tail.insert(0, ("mock", f"Mock paper, timed{short} (/tminus:mock)", mock_m))
    elif not on_last:
        days[-2]["mock_moved"] = mock_m
    reserve_last = sum(m for _, _, m in tail)

    queue = [dict(t, left=t["needed"]) for t in res["topics"] if t["tier"] != "X"]
    prev_titles = []
    for i, day in enumerate(days):
        cap_reserve = reserve_last if day is last else 0
        if day.get("mock_moved"):
            cap_reserve += day["mock_moved"]
        if prev_titles:
            rv = LAST_DAY_REVIEW if day is last else min(15 * len(prev_titles), 45)
            add(day, "review", "Spaced review: " + ", ".join(prev_titles), min(rv, day["free"] - cap_reserve))
        if i > 0 and day is not last:
            add(day, "drill", "Mixed drill across chapters (/tminus:drill mixed)", min(20, day["free"] - cap_reserve))
        today = []
        while queue and day["free"] - cap_reserve >= 10:
            t = queue[0]
            room = day["free"] - cap_reserve
            if t["left"] == t["needed"]:
                pm = min(t["needed"] * w["pack_share"], room)
                add(day, "pack", f"Pack: {t['id']} {t['title']} [tier {t['tier']}] (/tminus:pack {t['id']})", pm)
                t["left"] -= pm
                room = day["free"] - cap_reserve
            dm = min(t["left"], room)
            if dm > 0:
                add(day, "drill", f"Drill: {t['id']} {t['title']} (/tminus:drill {t['id']})", dm)
                t["left"] -= dm
            today.append(t["title"])
            if t["left"] <= 0.5:
                queue.pop(0)
            else:
                break
        if day["free"] - cap_reserve >= 10:
            add(day, "drill", "Drill weak items (/tminus:drill weak)", day["free"] - cap_reserve)
        if day.get("mock_moved"):
            add(day, "mock", "Mock paper, timed (/tminus:mock)", day["mock_moved"])
        if day is last:
            for kind, label, m in tail:
                add(day, kind, label, m)
            day["blocks"].append({"kind": "sleep", "label": "Sleep at least 7 hours. No new material tonight.",
                                  "minutes": 0})
        prev_titles = list(dict.fromkeys(today))
    exam = _dt(course["front"]["exam_datetime"])
    return {"days": days, "exam": exam.isoformat(),
            "unscheduled": [t["id"] for t in queue],
            "morning": "Exam morning: 20-30 min skim of the cram pack. No new material."}


def render_triage(course: dict, res: dict) -> str:
    b = res["budget"]
    L = [f"# Triage: {course['front']['course_code']} {course['front']['course_name']}", "",
         f"Generated {res['now']}. Rankings are heuristics from past-paper marks, lecture emphasis and your "
         "own ratings and drill results. Edit weights in `sprint/weights.json` if you disagree.", "",
         f"Study time until the exam: {b['available'] / 60:.1f} h. Reserved for mock, cram and spaced review: "
         f"{b['reserve'] / 60:.1f} h. Left for topics: {b['for_topics'] / 60:.1f} h.", "",
         "| rank | tier | chapter | expected marks | minutes | reason |", "|---|---|---|---|---|---|"]
    for i, t in enumerate(res["topics"], 1):
        L.append(f"| {i} | {t['tier']} | {t['id']} {t['title']} | {t['expected']:.1f} | {t['needed']:.0f} | {t['reason']} |")
    xs = [t for t in res["topics"] if t["tier"] == "X"]
    L += ["", "Tiers: A must do, B should do, C if time, X skip for now.", ""]
    if xs:
        L.append(f"**Cut line:** skipping {', '.join(t['id'] for t in xs)} gives up about "
                 f"{res['cut_cost']:.1f} expected marks per paper (on past-paper averages).")
    else:
        L.append("**Cut line:** everything fits in the time available.")
    if res["warnings"]:
        L += ["", "## Warnings"] + [f"- {x}" for x in res["warnings"]]
    return "\n".join(L) + "\n"


def render_plan(p: dict) -> str:
    L = ["# Day-by-day plan", "", "Re-run `/tminus:triage` each morning: it reads your drill results and "
         "rewrites the rest of this plan.", ""]
    for d in p["days"]:
        tot = sum(b["minutes"] for b in d["blocks"])
        L.append(f"## {d['date']} ({tot / 60:.1f} h)")
        for b in d["blocks"]:
            L.append(f"- {b['label']}" + (f" -- {b['minutes']} min" if b["minutes"] else ""))
        L.append("")
    if p.get("unscheduled"):
        L.append(f"Did not fit: {', '.join(p['unscheduled'])}. Do them only if blocks finish early.")
    L += [f"**Exam:** {p['exam']}", p.get("morning", "")]
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    opt = lambda k: argv[argv.index(k) + 1] if k in argv else None
    rd = lambda k: json.loads(Path(opt(k)).read_text()) if opt(k) else None
    course = load_valid(argv[0])
    wpath = Path(course["dir"]) / "sprint" / "weights.json"
    weights = rd("--weights") or (json.loads(wpath.read_text()) if wpath.is_file() else None)
    wm_default = Path(course["dir"]) / "progress" / "weakmap.json"
    weakmap = rd("--weakmap") or (json.loads(wm_default.read_text()) if wm_default.is_file() else None)
    res = score(course, now=opt("--now"), signals=rd("--signals"), weakmap=weakmap, weights=weights)
    p = plan(course, res)
    out = Path(opt("--out-dir") or Path(course["dir"]) / "sprint")
    out.mkdir(parents=True, exist_ok=True)
    (out / "triage.md").write_text(render_triage(course, res))
    (out / "plan.md").write_text(render_plan(p))
    (out / "triage.json").write_text(json.dumps({**res, "plan": p}, indent=2, default=str))
    if "--json" in argv:
        print(json.dumps(res, indent=2, default=str))
    else:
        print(render_triage(course, res))
        print(f"wrote {out / 'triage.md'}, {out / 'plan.md'}, {out / 'triage.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
