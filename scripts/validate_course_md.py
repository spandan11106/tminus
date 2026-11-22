#!/usr/bin/env python3
"""Validate and parse a tminus course.md.

Library:  load(path) -> dict   (raises CourseError on unparseable input)
          validate(path) -> list[str]   (empty list means valid)
CLI:      validate_course_md.py course.md [--json]
          exit 0 valid, 1 invalid (errors printed one per line).
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

SCHEMA_VERSION = 2
REQUIRED_FIELDS = ["course_code", "course_name", "schema_version", "exam_datetime",
                   "hours_per_day", "book_policy", "format"]
BOOK_POLICIES = {"closed", "open", "formula-sheet-allowed"}
FORMATS = {"pdf", "md"}
REQUIRED_SECTIONS = ["Book", "Chapters", "Professor conventions",
                     "Given vs must-remember formulas", "Verified corrections log"]
PAPER_RE = re.compile(r"^\s*(?P<paper>\S+)\s+(?P<q>[^()]+?)\s*\((?P<m>\d+(?:\.\d+)?)\)\s*$")


class CourseError(Exception):
    pass


def _split_front_matter(text: str):
    if not text.startswith("---"):
        raise CourseError("course.md must start with a '---' YAML front matter block")
    parts = text.split("\n---", 2)
    if len(parts) < 2:
        raise CourseError("front matter is not closed with '---'")
    fm_text = parts[0][3:]
    body = parts[1].split("\n", 1)[1] if "\n" in parts[1] else ""
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        raise CourseError(f"front matter is not valid YAML: {e}") from e
    if not isinstance(fm, dict):
        raise CourseError("front matter must be a mapping")
    return fm, body


def _sections(body: str) -> dict[str, str]:
    out, cur, buf = {}, None, []
    for line in body.splitlines():
        m = re.match(r"^##\s+(?!#)(.+?)\s*$", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = m.group(1), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def _find_section(secs: dict[str, str], name: str):
    for k, v in secs.items():
        if k.lower().startswith(name.lower()):
            return v
    return None


def _strip_comment(s: str) -> str:
    return re.sub(r"\s+#.*$", "", s).strip()


def _kv_bullets(sec: str) -> dict[str, str]:
    out = {}
    for line in sec.splitlines():
        m = re.match(r"^\s*-\s*([A-Za-z_]+)\s*:\s*(.*)$", line)
        if m:
            out[m.group(1)] = _strip_comment(m.group(2))
    return out


def _table_rows(sec: str) -> list[list[str]]:
    rows = []
    for line in sec.splitlines():
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    return rows[1:] if rows else []   # drop header


def parse_past_papers(cell: str) -> list[dict]:
    out = []
    for part in [p for p in re.split(r"[;\n]", cell) if p.strip() and p.strip() not in {"-", "none"}]:
        m = PAPER_RE.match(part)
        if not m:
            raise CourseError(f"cannot parse past-paper entry '{part.strip()}' "
                              "(expected '<paper> <question> (<marks>)')")
        out.append({"paper": m.group("paper"), "question": m.group("q").strip(),
                    "marks": float(m.group("m"))})
    return out


def _parse_pages(cell: str):
    m = re.fullmatch(r"\s*(\d+)\s*[-–]\s*(\d+)\s*", cell or "")
    return (int(m.group(1)), int(m.group(2))) if m else None


def load(path) -> dict:
    path = Path(path)
    fm, body = _split_front_matter(path.read_text(encoding="utf-8"))
    secs = _sections(body)
    book = _kv_bullets(_find_section(secs, "Book") or "")
    chapters = []
    for cells in _table_rows(_find_section(secs, "Chapters") or ""):
        cells += [""] * (7 - len(cells))
        cid, title, pages, lec, asg, papers, rating = cells[:7]
        chapters.append({
            "id": cid, "title": title, "pages_raw": pages, "pages": _parse_pages(pages),
            "lectures": [x.strip() for x in lec.split(",") if x.strip() and x.strip() != "-"],
            "assignments": [x.strip() for x in asg.split(",") if x.strip() and x.strip() != "-"],
            "past_papers_raw": papers, "rating_raw": rating,
        })
    return {"path": str(path), "dir": str(path.parent), "front": fm, "sections": secs,
            "book": book, "chapters": chapters}


def validate(path) -> list[str]:
    path = Path(path)
    if not path.is_file():
        return [f"{path}: file not found"]
    try:
        c = load(path)
    except CourseError as e:
        return [str(e)]
    errs = []
    fm = c["front"]
    for f in REQUIRED_FIELDS:
        if f not in fm or fm[f] in (None, ""):
            errs.append(f"front matter: missing field '{f}'")
    if "schema_version" in fm and fm["schema_version"] != SCHEMA_VERSION:
        errs.append(f"front matter: schema_version must be {SCHEMA_VERSION}")
    if fm.get("exam_datetime") not in (None, ""):
        try:
            v = fm["exam_datetime"]
            if not isinstance(v, (dt.datetime, dt.date)):
                dt.datetime.fromisoformat(str(v))
        except ValueError:
            errs.append("front matter: exam_datetime must be ISO format, e.g. 2026-11-25T09:30")
    if "hours_per_day" in fm:
        h = fm["hours_per_day"]
        if not isinstance(h, (int, float)) or not 0 < h <= 24:
            errs.append("front matter: hours_per_day must be a number in (0, 24]")
    if fm.get("book_policy") and fm["book_policy"] not in BOOK_POLICIES:
        errs.append(f"front matter: book_policy must be one of {sorted(BOOK_POLICIES)}")
    if fm.get("format") and fm["format"] not in FORMATS:
        errs.append(f"front matter: format must be one of {sorted(FORMATS)}")
    if "paper_total" in fm and not isinstance(fm["paper_total"], (int, float)):
        errs.append("front matter: paper_total must be a number")

    for s in REQUIRED_SECTIONS:
        if _find_section(c["sections"], s) is None:
            errs.append(f"missing section '## {s}'")

    book = c["book"]
    bp = book.get("path")
    if not bp:
        errs.append("Book: missing '- path:'")
    elif not (Path(c["dir"]) / bp).is_file():
        errs.append(f"Book: file not found: {bp}")
    off = book.get("page_offset")
    if off is None or not re.fullmatch(r"-?\d+", off):
        errs.append("Book: page_offset must be an integer")

    if not c["chapters"]:
        errs.append("Chapters: no chapter rows in the table")
    seen = set()
    for i, ch in enumerate(c["chapters"], 1):
        where = f"Chapters row {i}"
        if not ch["id"]:
            errs.append(f"{where}: missing id")
        elif ch["id"] in seen:
            errs.append(f"{where}: duplicate id '{ch['id']}'")
        seen.add(ch["id"])
        if not ch["title"]:
            errs.append(f"{where}: missing title")
        if ch["pages_raw"] and ch["pages"] is None:
            errs.append(f"{where}: book pages must look like '12-40'")
        r = ch["rating_raw"]
        if not re.fullmatch(r"[1-5]", r or ""):
            errs.append(f"{where}: self-rating must be an integer 1-5 (got '{r}')")
        try:
            parse_past_papers(ch["past_papers_raw"])
        except CourseError as e:
            errs.append(f"{where}: {e}")
    return errs


def load_valid(path) -> dict:
    """load() plus typed fields; raises CourseError listing all problems if invalid."""
    errs = validate(path)
    if errs:
        raise CourseError("course.md is invalid:\n  " + "\n  ".join(errs))
    c = load(path)
    c["book"]["page_offset"] = int(c["book"]["page_offset"])
    for ch in c["chapters"]:
        ch["self_rating"] = int(ch["rating_raw"])
        ch["past_papers"] = parse_past_papers(ch["past_papers_raw"])
    return c


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: validate_course_md.py course.md [--json]", file=sys.stderr)
        return 2
    errs = validate(argv[0])
    if errs:
        for e in errs:
            print(f"ERROR: {e}")
        return 1
    if "--json" in argv:
        c = load_valid(argv[0])
        c.pop("sections")
        print(json.dumps(c, indent=2, default=str))
    else:
        print(f"OK: {argv[0]} is valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
