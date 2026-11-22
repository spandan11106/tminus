#!/usr/bin/env python3
"""Recompute numeric claims and flag mismatches.

Input: a JSON list of claims, each
  {"id": "...", "expr": "16*T/(pi*d**3)"   (or "snippet": "python code that sets result"),
   "inputs": {"T": 1e6, "d": "50 mm"}, "claimed": 40.74 or "40.74 MPa",
   "rtol": 0.01 (default), "atol": 0 (default), "source": "Ex 3.2, printed p.81" (optional)}

- expr uses arithmetic and math functions only (sin, cos, tan, asin, acos, atan, atan2, sqrt, exp,
  log, log10, radians, degrees, pi, e, abs, min, max, round). sin/cos/tan take radians.
- Inputs or claimed values given as strings with units ("10 kN") are evaluated with pint when it is
  installed; the computed value is converted to the claimed unit before comparing.
- Default tolerance is 1 % relative (exam answers are rounded); set rtol per claim.

CLI: recompute.py claims.json [--corrections FILE] [--json]
     exit 0 all OK, 1 any MISMATCH, 2 any ERROR (bad input).
Never edits course.md: mismatches are appended to --corrections as candidate rows for the user
to confirm.
"""
from __future__ import annotations

import ast
import datetime as dt
import json
import math
import sys
from pathlib import Path

try:
    import pint
    UREG = pint.UnitRegistry()
except ImportError:                    # pint is optional
    pint = None
    UREG = None

FUNCS = {n: getattr(math, n) for n in ("sin", "cos", "tan", "asin", "acos", "atan", "atan2", "sqrt",
                                       "exp", "log", "log10", "radians", "degrees", "hypot", "floor",
                                       "ceil")}
FUNCS.update({"abs": abs, "min": min, "max": max, "round": round})
CONSTS = {"pi": math.pi, "e": math.e}
SAFE_NODES = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Call, ast.Name, ast.Load, ast.Constant,
              ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod, ast.FloorDiv, ast.USub,
              ast.UAdd, ast.Tuple, ast.keyword)


class ClaimError(Exception):
    pass


def _quantity(v):
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str):
        if UREG is None:
            try:
                return float(v)
            except ValueError:
                raise ClaimError(f"value '{v}' has units but pint is not installed") from None
        return UREG.Quantity(v)
    raise ClaimError(f"unsupported value {v!r}")


def _safe_eval(expr: str, names: dict):
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, SAFE_NODES):
            raise ClaimError(f"disallowed syntax in expr: {type(node).__name__}")
        if isinstance(node, ast.Call) and not (isinstance(node.func, ast.Name) and node.func.id in FUNCS):
            raise ClaimError("only whitelisted math functions may be called")
        if isinstance(node, ast.Name) and node.id not in names and node.id not in FUNCS \
                and node.id not in CONSTS:
            raise ClaimError(f"unknown name '{node.id}'")
    env = {**CONSTS, **FUNCS, **names}
    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, env)


def _run_snippet(code: str, names: dict):
    ns = {**CONSTS, **FUNCS, "math": math, **names}
    exec(compile(code, "<snippet>", "exec"), {"__builtins__": __builtins__}, ns)
    if "result" not in ns:
        raise ClaimError("snippet must set 'result'")
    return ns["result"]


def check(c: dict) -> dict:
    cid = c.get("id", "?")
    out = {"id": cid, "source": c.get("source", ""), "claimed": c.get("claimed")}
    try:
        names = {k: _quantity(v) for k, v in (c.get("inputs") or {}).items()}
        if "expr" in c:
            val = _safe_eval(c["expr"], names)
        elif "snippet" in c:
            val = _run_snippet(c["snippet"], names)
        else:
            raise ClaimError("claim needs 'expr' or 'snippet'")
        claimed = _quantity(c["claimed"])
        if pint is not None and isinstance(claimed, UREG.Quantity):
            if not isinstance(val, UREG.Quantity):
                raise ClaimError("claimed value has units but the computed value has none")
            val = val.to(claimed.units)
            unit = f" {claimed.units:~}"
            val, claimed = val.magnitude, claimed.magnitude
        else:
            if pint is not None and isinstance(val, UREG.Quantity):
                val = val.to_base_units().magnitude if not val.dimensionless else val.magnitude
            unit = ""
        val, claimed = float(val), float(claimed)
    except Exception as e:  # report every failure as ERROR with its reason
        out.update(status="ERROR", computed=None, note=f"{type(e).__name__}: {e}")
        return out
    rtol, atol = float(c.get("rtol", 0.01)), float(c.get("atol", 0.0))
    ok = math.isclose(val, claimed, rel_tol=rtol, abs_tol=atol)
    note = ""
    if not ok and claimed and val:
        ratio = claimed / val
        for k in (-3, -2, -1, 1, 2, 3):
            if math.isclose(ratio, 10 ** k, rel_tol=rtol * 2):
                note = f"claimed is x10^{k} of computed (decimal-point slip?)" if abs(k) > 1 else \
                       f"claimed is x10{'' if k > 0 else '^-1'} of computed (decimal-point slip?)"
    out.update(status="OK" if ok else "MISMATCH", computed=val, unit=unit, note=note)
    return out


def _fmt(x):
    return "-" if x is None else f"{x:.6g}"


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print(__doc__, file=sys.stderr)
        return 2
    claims = json.loads(Path(argv[0]).read_text())
    if isinstance(claims, dict):
        claims = [claims]
    results = [check(c) for c in claims]
    if "--json" in argv:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            line = f"{r['status']} {r['id']}: computed {_fmt(r['computed'])}{r.get('unit', '')}"
            line += f", claimed {r['claimed']}"
            if r.get("source"):
                line += f"  [{r['source']}]"
            if r.get("note"):
                line += f"  -- {r['note']}"
            print(line)
        n = {s: sum(r["status"] == s for r in results) for s in ("OK", "MISMATCH", "ERROR")}
        print(f"recompute: {len(results)} checked, {n['OK']} OK, {n['MISMATCH']} MISMATCH, {n['ERROR']} ERROR")
    if "--corrections" in argv:
        mism = [r for r in results if r["status"] == "MISMATCH"]
        if mism:
            f = Path(argv[argv.index("--corrections") + 1])
            new = not f.exists()
            with f.open("a") as fh:
                if new:
                    fh.write("# Candidate corrections (confirm before copying into course.md)\n\n"
                             "| date | location | book/slide says | correct value | how verified |\n"
                             "|------|----------|-----------------|---------------|--------------|")
                for r in mism:
                    fh.write(f"\n| {dt.date.today().isoformat()} | {r['source'] or r['id']} | "
                             f"{r['claimed']} | {_fmt(r['computed'])}{r.get('unit', '')} | "
                             f"recompute.py ({r['id']}){'; ' + r['note'] if r['note'] else ''} |")
                fh.write("\n")
    if any(r["status"] == "ERROR" for r in results):
        return 2
    return 1 if any(r["status"] == "MISMATCH" for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
