#!/usr/bin/env python3
"""Parse and validate the fenced-json output of the verifier and recomputer subagents.

CLI: agent_output.py verifier|recomputer FILE   -> prints a summary; exit 1 if any row needs action.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

SCHEMAS = {
    "verifier": ({"id", "status", "source", "evidence", "correct"},
                 {"MATCH", "MISMATCH", "SOURCE_ERROR", "NOT_FOUND"}),
    "recomputer": ({"id", "status", "computed", "claimed"}, {"OK", "MISMATCH", "ERROR"}),
}
NEEDS_ACTION = {"MISMATCH", "SOURCE_ERROR", "NOT_FOUND", "ERROR"}


def parse(text: str, kind: str) -> list[dict]:
    blocks = re.findall(r"```json\s*\n(.*?)```", text, flags=re.S)
    if not blocks:
        raise ValueError("no ```json block in agent output")
    rows = json.loads(blocks[-1])
    if not isinstance(rows, list):
        raise ValueError("agent output must be a JSON list")
    keys, statuses = SCHEMAS[kind]
    for i, r in enumerate(rows):
        missing = keys - set(r)
        if missing:
            raise ValueError(f"row {i}: missing {sorted(missing)}")
        if r["status"] not in statuses:
            raise ValueError(f"row {i}: status {r['status']!r} not in {sorted(statuses)}")
    return rows


def summary(rows) -> dict:
    return dict(Counter(r["status"] for r in rows))


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 2 or argv[0] not in SCHEMAS:
        print(__doc__, file=sys.stderr)
        return 2
    try:
        rows = parse(Path(argv[1]).read_text(), argv[0])
    except (ValueError, json.JSONDecodeError) as e:
        print(f"ERROR: {e}")
        return 2
    print(", ".join(f"{k} {v}" for k, v in summary(rows).items()))
    for r in rows:
        if r["status"] in NEEDS_ACTION:
            print(f"{r['status']} {r['id']}: {r.get('correct') or r.get('note') or r.get('evidence', '')}")
    return 1 if any(r["status"] in NEEDS_ACTION for r in rows) else 0


if __name__ == "__main__":
    sys.exit(main())
