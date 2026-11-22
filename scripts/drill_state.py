#!/usr/bin/env python3
"""Drill state: attempts log, mistakes list, weak-topic map and review queue.

Files in the progress dir:
  attempts.jsonl  one JSON object per attempt (append only)
  errors.md       mistakes the student keeps making, grouped and counted
  weakmap.md      chapters ranked weakest first (human readable)
  weakmap.json    the same, for triage_score.py

Results: correct (1.0), partial (0.5), hesitant (0.5: right but slow/unsure), wrong (0.0).
Scheduling (Leitner-lite, tuned for a 72-hour window): box 0 = due now, box 1 = next day (20 h),
box 2 = +44 h, box 3 = +68 h. correct -> box+1; hesitant -> box 1; wrong/partial -> box 0, and the
item is shown again in the same session only after at least GAP other items. An item that was
wrong in the last 24 h stays capped at box 1, so it comes back the next day even if later right.

CLI:
  drill_state.py log --dir D --chapter C --item ID --kind theory|numerical --result R
                     [--note TEXT] [--mode M] [--source S] [--now ISO]
  drill_state.py rebuild --dir D
  drill_state.py queue --dir D [--now ISO] [--chapter C] [--limit N]
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCORE = {"correct": 1.0, "partial": 0.5, "hesitant": 0.5, "wrong": 0.0}
KINDS = {"theory", "numerical"}
INTERVALS = [dt.timedelta(0), dt.timedelta(hours=20), dt.timedelta(hours=44), dt.timedelta(hours=68)]
GAP = 3
RECENT = 10


def _now(now=None) -> dt.datetime:
    if now is None:
        return dt.datetime.now().replace(microsecond=0)
    return now if isinstance(now, dt.datetime) else dt.datetime.fromisoformat(now)


def log_attempt(d, rec: dict, now=None) -> dict:
    d = Path(d)
    if rec.get("result") not in SCORE:
        raise ValueError(f"result must be one of {sorted(SCORE)}")
    if rec.get("kind") not in KINDS:
        raise ValueError(f"kind must be one of {sorted(KINDS)}")
    for k in ("chapter", "item"):
        if not rec.get(k):
            raise ValueError(f"missing {k}")
    d.mkdir(parents=True, exist_ok=True)
    rec = {"ts": _now(now).isoformat(), **{k: v for k, v in rec.items() if v not in (None, "")}}
    rec["chapter"] = str(rec["chapter"])
    with (d / "attempts.jsonl").open("a") as fh:
        fh.write(json.dumps(rec) + "\n")
    return rec


def attempts(d) -> list[dict]:
    f = Path(d) / "attempts.jsonl"
    if not f.is_file():
        return []
    out = []
    for i, line in enumerate(f.read_text().splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"{f}:{i}: bad JSON: {e}") from e
    return out


def item_states(atts: list[dict]) -> dict:
    st = {}
    for a in atts:
        ts = dt.datetime.fromisoformat(a["ts"])
        s = st.setdefault(a["item"], {"item": a["item"], "chapter": a["chapter"],
                                      "kind": a.get("kind"), "box": 0, "last_wrong": None, "n": 0})
        s["n"] += 1
        r = a["result"]
        if r == "correct":
            s["box"] = min(s["box"] + 1, 3)
        elif r == "hesitant":
            s["box"] = 1
        else:
            s["box"] = 0
            s["last_wrong"] = ts
        if s["last_wrong"] and ts - s["last_wrong"] < dt.timedelta(hours=24):
            s["box"] = min(s["box"], 1)
        s["last"], s["last_result"] = ts, r
        s["due"] = ts + INTERVALS[s["box"]]
    return st


def queue(d, now=None, chapter=None, limit=None) -> list[dict]:
    now = _now(now)
    atts = attempts(d)
    st = item_states(atts)
    due = [s for s in st.values() if s["due"] <= now and (chapter is None or s["chapter"] == str(chapter))]
    # wrong first, then partial/hesitant, then plain reviews; oldest first within a group
    rank = {"wrong": 0, "partial": 1, "hesitant": 1, "correct": 2}
    due.sort(key=lambda s: (rank[s["last_result"]], s["last"]))
    # keep a gap: the most recently attempted items go no earlier than position GAP
    recent_order = [a["item"] for a in atts][-GAP:]
    fresh = [s for s in due if s["item"] in recent_order]
    rest = [s for s in due if s["item"] not in recent_order]
    for s in sorted(fresh, key=lambda s: recent_order.index(s["item"])):
        rest.insert(min(GAP, len(rest)), s)
    out = [{"item": s["item"], "chapter": s["chapter"], "kind": s["kind"],
            "last_result": s["last_result"], "box": s["box"]} for s in rest]
    return out[:limit] if limit else out


def _norm(note: str) -> str:
    return re.sub(r"\s+", " ", note.strip().lower().rstrip("."))


def rebuild(d) -> dict:
    d = Path(d)
    atts = attempts(d)
    by_ch = defaultdict(list)
    for a in atts:
        by_ch[a["chapter"]].append(a)
    chapters = []
    for ch, lst in by_ch.items():
        scores = [SCORE[a["result"]] for a in lst]
        recent = scores[-RECENT:]
        acc = sum(recent) / len(recent)
        kinds = {}
        for k in KINDS:
            ks = [SCORE[a["result"]] for a in lst if a.get("kind") == k]
            if ks:
                kinds[k] = round(sum(ks) / len(ks), 3)
        chapters.append({"chapter": ch, "attempts": len(lst), "accuracy_all": round(sum(scores) / len(scores), 3),
                         "accuracy": round(acc, 3), "weakness": round(1 - acc, 3), "by_kind": kinds})
    chapters.sort(key=lambda c: (-c["weakness"], -c["attempts"], c["chapter"]))
    wm = {"updated": _now().isoformat(), "recent_window": RECENT, "chapters": chapters}
    (d / "weakmap.json").write_text(json.dumps(wm, indent=2))

    md = ["# Weak-topic map", "", f"Weakest first. Accuracy is over each chapter's last {RECENT} attempts.", "",
          "| rank | chapter | attempts | accuracy (recent) | accuracy (all) | theory | numerical |",
          "|---|---|---|---|---|---|---|"]
    for i, c in enumerate(chapters, 1):
        pct = lambda k: format(c["by_kind"][k], ".0%") if k in c["by_kind"] else "-"
        md.append(f"| {i} | {c['chapter']} | {c['attempts']} | {c['accuracy']:.0%} | "
                  f"{c['accuracy_all']:.0%} | {pct('theory')} | {pct('numerical')} |")
    (d / "weakmap.md").write_text("\n".join(md) + "\n")

    groups = {}
    for a in atts:
        if a["result"] in ("wrong", "partial") and a.get("note"):
            k = _norm(a["note"])
            g = groups.setdefault(k, {"note": a["note"].strip(), "count": 0, "chapters": set(),
                                      "items": [], "last": a["ts"]})
            g["count"] += 1
            g["chapters"].add(a["chapter"])
            g["items"].append(a["item"])
            g["last"] = max(g["last"], a["ts"])
    ranked = sorted(groups.values(), key=lambda g: (g["count"], g["last"]), reverse=True)
    em = ["# Mistakes you keep making", "",
          "Grouped from drill attempts marked wrong or partial. Most repeated first.", ""]
    if not ranked:
        em.append("(none recorded yet)")
    for i, g in enumerate(ranked, 1):
        em.append(f"{i}. {g['note']} -- x{g['count']} (chapter {', '.join(sorted(g['chapters']))}; "
                  f"items {', '.join(dict.fromkeys(g['items']))})")
    (d / "errors.md").write_text("\n".join(em) + "\n")
    return wm


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="drill_state.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    lg = sub.add_parser("log")
    lg.add_argument("--dir", required=True)
    lg.add_argument("--chapter", required=True)
    lg.add_argument("--item", required=True)
    lg.add_argument("--kind", required=True)
    lg.add_argument("--result", required=True)
    for opt in ("--note", "--mode", "--source", "--now"):
        lg.add_argument(opt)
    rb = sub.add_parser("rebuild")
    rb.add_argument("--dir", required=True)
    qu = sub.add_parser("queue")
    qu.add_argument("--dir", required=True)
    qu.add_argument("--now")
    qu.add_argument("--chapter")
    qu.add_argument("--limit", type=int)
    a = p.parse_args(argv)
    try:
        if a.cmd == "log":
            rec = log_attempt(a.dir, {"chapter": a.chapter, "item": a.item, "kind": a.kind,
                                      "result": a.result, "note": a.note, "mode": a.mode,
                                      "source": a.source}, now=a.now)
            print(f"logged {rec['item']} ({rec['result']})")
        elif a.cmd == "rebuild":
            wm = rebuild(a.dir)
            print("weakest first: " + ", ".join(f"{c['chapter']} ({c['accuracy']:.0%})" for c in wm["chapters"]))
        else:
            q = queue(a.dir, now=a.now, chapter=a.chapter, limit=a.limit)
            print(json.dumps(q, indent=1) if q else "queue empty")
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
