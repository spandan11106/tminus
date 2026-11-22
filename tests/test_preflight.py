"""Simulated environments: restricted PATH with stub tools, fake os-release, fake missing modules."""
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts" / "preflight.py"
OSREL = ROOT / "tests" / "fixtures" / "os-release"
ALL_TOOLS = ["latexmk", "pdflatex", "kpsewhich", "pdftotext", "pdftoppm"]


def stub(bindir: Path, name: str, body: str = "exit 0"):
    p = bindir / name
    p.write_text(f"#!/bin/sh\n{body}\n")
    p.chmod(p.stat().st_mode | stat.S_IEXEC)


def env_with(tmp_path, tools, os_name="arch", missing_modules="", missing_sty=()):
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    for t in tools:
        if t == "kpsewhich":
            cases = " ".join(f"{s}.sty) exit 1;;" for s in missing_sty)
            stub(bindir, t, f'case "$1" in {cases} *) echo "/fake/$1";; esac')
        else:
            stub(bindir, t, 'echo "fake 1.0"')
    env = {"PATH": str(bindir), "HOME": str(tmp_path),
           "TMINUS_OS_RELEASE": str(OSREL / os_name), "TMINUS_UNAME": "Linux 6.0-generic",
           "TMINUS_FAKE_MISSING_MODULES": missing_modules}
    return env


def run(env, *args):
    r = subprocess.run([sys.executable, str(PREFLIGHT), *args], env=env,
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def run_json(env):
    code, out = run(env, "--json")
    return code, json.loads(out)


def test_everything_present(tmp_path):
    code, res = run_json(env_with(tmp_path, ALL_TOOLS, missing_modules="pint"))
    assert code == 2                      # an optional module missing
    code, res = run_json(env_with(tmp_path, ALL_TOOLS, missing_modules=""))
    assert code == 0
    assert res["engine"] == "latexmk"
    assert res["format_recommended"] == "pdf"
    req = [i for i in res["items"] if i["tier"] == "required"]
    assert all(i["status"] == "OK" for i in req)


def test_no_tex_degrades_to_md(tmp_path):
    code, out = run(env_with(tmp_path, ["pdftotext", "pdftoppm"]))
    assert code == 2
    assert "format: md" in out
    assert "sudo pacman -S --needed texlive-basic" in out


def test_no_python_deps_is_required_failure(tmp_path):
    env = env_with(tmp_path, ["latexmk", "pdflatex", "kpsewhich"],
                   missing_modules="yaml,pymupdf,fitz")
    code, out = run(env)
    assert code == 1
    assert "pip install -r" in out and "requirements.txt" in out
    assert "MISSING" in out


def test_unknown_os_has_no_fix_but_names_items(tmp_path):
    code, out = run(env_with(tmp_path, ["pdftotext"], os_name="unknown"))
    assert code == 2
    assert "OS: unknown" in out
    assert "install manually" in out


def test_missing_latex_package_arch(tmp_path):
    code, out = run(env_with(tmp_path, ALL_TOOLS, missing_sty=("tcolorbox", "siunitx")))
    assert code == 2
    assert "missing: siunitx, tcolorbox" in out
    assert "sudo pacman -S --needed texlive-latexextra texlive-mathscience" in out


def test_missing_latex_package_debian_and_fedora(tmp_path):
    _, out = run(env_with(tmp_path, ALL_TOOLS, os_name="ubuntu", missing_sty=("tcolorbox",)))
    assert "sudo apt install texlive-latex-extra" in out
    _, out = run(env_with(tmp_path, ALL_TOOLS, os_name="fedora", missing_sty=("tcolorbox",)))
    assert "sudo dnf install 'tex(tcolorbox.sty)'" in out


def test_macos_and_wsl_and_windows(tmp_path):
    env = env_with(tmp_path, ["pdftotext"]); env["TMINUS_UNAME"] = "Darwin 24.0"
    _, out = run(env)
    assert "OS: macos" in out and "brew install tectonic" in out
    env["TMINUS_UNAME"] = "Linux 5.15.0-microsoft-standard-WSL2"
    _, out = run(env)
    assert "OS: wsl" in out and "sudo apt install" in out
    env["TMINUS_UNAME"] = "Windows 10"
    _, out = run(env)
    assert "WSL2" in out


def test_tectonic_only(tmp_path):
    code, res = run_json(env_with(tmp_path, ["tectonic", "pdftotext"]))
    assert res["engine"] == "tectonic"
    pk = [i for i in res["items"] if i["name"].startswith("LaTeX packages")][0]
    assert pk["status"] == "OK"


def test_cache_and_fast_path(tmp_path):
    env = env_with(tmp_path, ALL_TOOLS)
    cache = tmp_path / ".tminus"
    run(env, "--cache-dir", str(cache))
    data = json.loads((cache / "preflight.json").read_text())
    assert data["os_class"] == "arch"
    code, out = run(env, "--fast", "--cache-dir", str(cache))
    assert "cached result" in out
    # a cached tool disappears -> full re-check
    (tmp_path / "bin" / "latexmk").unlink()
    code, out = run(env, "--fast", "--cache-dir", str(cache))
    assert "cached result" not in out and "tminus doctor" in out


def test_template_packages_scan():
    sys.path.insert(0, str(ROOT / "scripts"))
    import preflight
    pkgs = preflight.template_packages()
    assert "tcolorbox" in pkgs and "tminus" not in pkgs
    assert all(p in preflight.TEXPKG for p in pkgs), "every template package needs install hints"
