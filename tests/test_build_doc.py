import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_doc.sh"
STRESS = ROOT / "tests" / "fixtures" / "stress"
HAS_TEX = bool(shutil.which("latexmk") or shutil.which("tectonic") or shutil.which("pdflatex"))
needs_tex = pytest.mark.skipif(not HAS_TEX, reason="no TeX engine (PDF gate PENDING)")


def build(src, *args, env=None):
    r = subprocess.run([shutil.which("bash") or "/bin/bash", str(BUILD), str(src), *args], capture_output=True, text=True,
                       env=env or os.environ.copy())
    return r.returncode, r.stdout + r.stderr


def fill(template: Path, dest: Path) -> Path:
    text = re.sub(r"<<[A-Z_]+[^>]*>>", "x", template.read_text())
    dest.write_text(text)
    return dest


def test_placeholder_gate(tmp_path):
    src = tmp_path / "pack.tex"; shutil.copy(ROOT / "templates" / "pack.tex", src)
    code, out = build(src)
    assert code == 1 and "Placeholder gate FAILED" in out


def test_nonascii_rejected(tmp_path):
    code, out = build(STRESS / "nonascii.tex", "--out", str(tmp_path))
    assert code == 1 and "ASCII gate FAILED" in out and "$\\sigma$" in out
    assert not list(tmp_path.glob("*.pdf"))


@needs_tex
@pytest.mark.parametrize("name", ["pack.tex", "cram.tex"])
def test_templates_compile_when_filled(tmp_path, name):
    src = fill(ROOT / "templates" / name, tmp_path / name)
    code, out = build(src)
    assert code == 0, out
    assert (tmp_path / name.replace(".tex", ".pdf")).is_file()
    assert "engine: " in out


@needs_tex
def test_stress_clash_and_long_header(tmp_path):
    src = tmp_path / "clash.tex"; shutil.copy(STRESS / "clash.tex", src)
    code, out = build(src)
    assert code == 0, out
    assert "WARNING: header taller" not in out
    log_free = not list(tmp_path.glob("*.log"))
    assert log_free, "aux files must not be left next to the output"


@needs_tex
def test_overfull_gate_fails_and_leaves_no_pdf(tmp_path):
    code, out = build(STRESS / "overfull.tex", "--out", str(tmp_path))
    assert code == 1 and "Overfull gate FAILED" in out
    assert not list(tmp_path.glob("*.pdf"))


def test_no_engine_exit_3_and_md_mode_works(tmp_path):
    env = os.environ.copy()
    env["PATH"] = "/usr/bin/nonexistent"           # no TeX, no pandoc
    env["TMINUS_VENV"] = str(tmp_path / "novenv")
    pybin = Path(shutil.which("python3")).parent
    shim = tmp_path / "bin"; shim.mkdir()
    for tool in ("python3", "grep", "cp", "mkdir", "dirname", "basename", "mktemp", "rm", "mv", "bash"):
        p = shutil.which(tool)
        if p:
            (shim / tool).symlink_to(p)
    env["PATH"] = str(shim)
    src = fill(ROOT / "templates" / "pack.tex", tmp_path / "p.tex")
    code, out = build(src, env=env)
    assert code == 3 and "format: md" in out
    md = tmp_path / "p.md"; md.write_text("# Pack\n\nSome $x$ text.\n")
    outdir = tmp_path / "out"
    code, out = build(md, "--out", str(outdir), env=env)
    assert code == 0, out
    assert "engine: markdown" in out and (outdir / "p.md").is_file()
