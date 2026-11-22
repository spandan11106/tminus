import json

import pytest

import recompute as rc


def claim(**kw):
    base = {"id": "c1", "expr": "F / A", "inputs": {"F": 10000, "A": 800}, "claimed": 12.5}
    base.update(kw)
    return base


def test_ok_within_tolerance():
    r = rc.check(claim(claimed=12.51))
    assert r["status"] == "OK" and abs(r["computed"] - 12.5) < 1e-12


def test_mismatch_decimal_typo():
    r = rc.check(claim(claimed=125))
    assert r["status"] == "MISMATCH" and "x10" in r["note"]


def test_math_functions_and_degrees():
    r = rc.check({"id": "t", "expr": "16*T/(pi*d**3)", "inputs": {"T": 1e6, "d": 50},
                  "claimed": 40.74})
    assert r["status"] == "OK"
    r = rc.check({"id": "e", "expr": "exp(mu*radians(theta))", "inputs": {"mu": 0.3, "theta": 180},
                  "claimed": 2.566})
    assert r["status"] == "OK"


def test_rejects_unsafe_expression():
    r = rc.check(claim(expr="__import__('os').system('true')"))
    assert r["status"] == "ERROR"


def test_snippet():
    r = rc.check({"id": "s", "snippet": "n = 0\nfor i in range(4):\n    n += F\nresult = n",
                  "inputs": {"F": 2.5}, "claimed": 10})
    assert r["status"] == "OK"


def test_units_with_pint():
    pytest.importorskip("pint")
    r = rc.check({"id": "u", "expr": "F / A", "inputs": {"F": "10 kN", "A": "800 mm**2"},
                  "claimed": "12.5 MPa"})
    assert r["status"] == "OK", r
    r = rc.check({"id": "u2", "expr": "F / A", "inputs": {"F": "10 kN", "A": "800 mm**2"},
                  "claimed": "12.5 kPa"})
    assert r["status"] == "MISMATCH"


def test_cli_and_corrections_file(tmp_path, capsys):
    f = tmp_path / "claims.json"
    f.write_text(json.dumps([claim(), claim(id="bad", claimed=1.25, source="Ex 12.14 p.480")]))
    corr = tmp_path / "corrections.md"
    code = rc.main([str(f), "--corrections", str(corr)])
    out = capsys.readouterr().out
    assert code == 1
    assert "OK c1" in out and "MISMATCH bad" in out
    text = corr.read_text()
    assert "Ex 12.14 p.480" in text and "12.5" in text
    assert text.count("recompute.py (") == 1   # only the mismatch is a candidate


def test_tolerance_override():
    assert rc.check(claim(claimed=13.0, rtol=0.05))["status"] == "OK"
    assert rc.check(claim(claimed=13.0))["status"] == "MISMATCH"
