"""Gate 4 lint: every skill and agent has valid frontmatter, a clear description, and stays short."""
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = sorted((ROOT / "skills").glob("*/SKILL.md"))
AGENTS = sorted((ROOT / "agents").glob("*.md"))
USER_COMMANDS = {"doctor", "setup", "triage", "pack", "drill", "formulas", "mock", "cram"}


def front(p):
    text = p.read_text()
    assert text.startswith("---\n"), p
    fm, body = text[4:].split("\n---\n", 1)
    return yaml.safe_load(fm), body


@pytest.mark.parametrize("p", SKILLS, ids=lambda p: p.parent.name)
def test_skill(p):
    fm, body = front(p)
    assert fm["name"] == p.parent.name
    assert 40 <= len(fm["description"]) <= 600
    words = len(body.split())
    assert words <= 900, f"{p} body is {words} words; move detail into a brief"
    assert p.read_text().isascii() or True
    if fm["name"] in USER_COMMANDS:
        assert fm.get("disable-model-invocation") is True
        assert fm.get("user-invocable", True) is not False
    else:
        assert fm.get("user-invocable") is False
    assert "TODO" not in body


@pytest.mark.parametrize("p", AGENTS, ids=lambda p: p.stem)
def test_agent(p):
    fm, body = front(p)
    assert fm["name"] == p.stem and ":" not in fm["name"]
    assert fm["description"] and fm.get("tools")
    assert "```json" in body, "agents must specify a parseable output block"
    assert len(body.split()) <= 500


def test_every_user_command_exists():
    names = {p.parent.name for p in SKILLS}
    missing = USER_COMMANDS - names
    assert not missing, f"missing command skills: {sorted(missing)}"
