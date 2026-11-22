import pytest

import agent_output as ao

VERIFIER = """Some chatter the agent should not have written.
```json
[{"id": "c1", "status": "MATCH", "source": "book p. 141", "evidence": "q", "correct": null},
 {"id": "c2", "status": "SOURCE_ERROR", "source": "book p. 480", "evidence": "16792/(m c)", "correct": "7.3 C"}]
```
"""
RECOMP = """```json
[{"id": "a", "status": "OK", "computed": 12.5, "claimed": 12.5, "note": ""}]
```"""


def test_parse_verifier():
    rows = ao.parse(VERIFIER, "verifier")
    assert [r["status"] for r in rows] == ["MATCH", "SOURCE_ERROR"]
    assert ao.summary(rows) == {"MATCH": 1, "SOURCE_ERROR": 1}


def test_parse_recomputer():
    assert ao.parse(RECOMP, "recomputer")[0]["status"] == "OK"


def test_rejects_bad_status_and_missing_block():
    with pytest.raises(ValueError):
        ao.parse('```json\n[{"id": "x", "status": "MAYBE", "source": "", "evidence": "", "correct": null}]\n```', "verifier")
    with pytest.raises(ValueError):
        ao.parse("no json here", "verifier")
    with pytest.raises(ValueError):
        ao.parse('```json\n[{"id": "x"}]\n```', "recomputer")
