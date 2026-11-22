import json

import drill_state as ds

T0 = "2026-11-28T10:00:00"


def log(d, item, result, ch="1", note="", kind="theory", now=T0):
    ds.log_attempt(d, {"chapter": ch, "item": item, "kind": kind, "result": result,
                       "note": note}, now=now)


def test_log_appends_jsonl(tmp_path):
    log(tmp_path, "1-a", "correct")
    log(tmp_path, "1-b", "wrong", note="sign error")
    lines = (tmp_path / "attempts.jsonl").read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[1])["result"] == "wrong"


def test_wrong_answer_requeued_same_session_after_gap(tmp_path):
    for i in "abcde":
        log(tmp_path, f"1-{i}", "wrong" if i == "a" else "hesitant")
    q = ds.queue(tmp_path, now="2026-11-28T10:05:00")
    ids = [x["item"] for x in q]
    assert "1-a" in ids
    assert ids.index("1-a") >= 3 or len(ids) <= 3     # not shown again immediately


def test_correct_item_due_next_day_not_now(tmp_path):
    log(tmp_path, "1-a", "correct")
    assert ds.queue(tmp_path, now="2026-11-28T10:30:00") == []
    q = ds.queue(tmp_path, now="2026-11-29T08:00:00")
    assert [x["item"] for x in q] == ["1-a"]


def test_wrong_then_correct_still_reviewed_next_day(tmp_path):
    log(tmp_path, "1-a", "wrong")
    log(tmp_path, "1-a", "correct", now="2026-11-28T10:10:00")
    assert ds.queue(tmp_path, now="2026-11-28T10:20:00") == []
    assert [x["item"] for x in ds.queue(tmp_path, now="2026-11-29T07:00:00")] == ["1-a"]


def test_weakmap_order_changes(tmp_path):
    for i in range(4):
        log(tmp_path, f"1-{i}", "correct", ch="1")
        log(tmp_path, f"2-{i}", "wrong", ch="2", note="forgot Wahl factor")
    wm = ds.rebuild(tmp_path)
    assert [c["chapter"] for c in wm["chapters"]][:2] == ["2", "1"]
    for i in range(6):
        log(tmp_path, f"2-x{i}", "correct", ch="2", now="2026-11-29T10:00:00")
        log(tmp_path, f"1-x{i}", "wrong", ch="1", now="2026-11-29T10:00:00", note="units")
    wm = ds.rebuild(tmp_path)
    assert [c["chapter"] for c in wm["chapters"]][:2] == ["1", "2"]
    assert (tmp_path / "weakmap.md").is_file() and (tmp_path / "weakmap.json").is_file()


def test_errors_md_groups_repeated_mistakes(tmp_path):
    log(tmp_path, "2-a", "wrong", ch="2", note="Forgot Wahl factor")
    log(tmp_path, "2-b", "wrong", ch="2", note="forgot wahl factor ")
    log(tmp_path, "3-a", "partial", ch="3", note="units of torque")
    ds.rebuild(tmp_path)
    text = (tmp_path / "errors.md").read_text()
    first = [l for l in text.splitlines() if l.startswith("1.")][0]
    assert "wahl factor" in first.lower() and "x2" in first


def test_cli_roundtrip(tmp_path, capsys):
    assert ds.main(["log", "--dir", str(tmp_path), "--chapter", "1", "--item", "1-a",
                    "--kind", "numerical", "--result", "wrong", "--note", "used book C",
                    "--now", T0]) == 0
    assert ds.main(["rebuild", "--dir", str(tmp_path)]) == 0
    assert ds.main(["queue", "--dir", str(tmp_path), "--now", T0]) == 0
    assert "1-a" in capsys.readouterr().out
    assert ds.main(["log", "--dir", str(tmp_path), "--chapter", "1", "--item", "x",
                    "--kind", "theory", "--result", "maybe"]) == 2
