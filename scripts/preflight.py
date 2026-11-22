#!/usr/bin/env python3
"""tminus runtime preflight (surfaced as /tminus:doctor).

Usage:
  preflight.py [--json] [--cache-dir DIR] [--fast] [--install [--yes]]

Exit codes: 0 all required present; 1 a required item is missing;
            2 only optional or degradable items are missing.

Test hooks (environment variables):
  TMINUS_OS_RELEASE         path used instead of /etc/os-release
  TMINUS_UNAME              "<system> <release>" used instead of os.uname()
  TMINUS_FAKE_MISSING_MODULES  comma list of Python modules to treat as missing
  TMINUS_TEMPLATES_DIR      directory scanned for LaTeX packages
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "tminus"
CACHE_MAX_AGE = dt.timedelta(days=7)
LOCAL_PACKAGES = {"tminus"}          # shipped with the plugin, not from TeX Live

# ---------------------------------------------------------------- install hints
# Every name here was checked against the distro's package index; see docs/DECISIONS.md
# (entries marked UNVERIFIED there could not be checked).
SYS = {
    "arch": {
        "python3": "sudo pacman -S --needed python",
        "pdftotext": "sudo pacman -S --needed poppler",
        "pdftoppm": "sudo pacman -S --needed poppler",
        "latexmk": "sudo pacman -S --needed texlive-binextra",
        "tex": "sudo pacman -S --needed texlive-basic texlive-latex texlive-latexrecommended "
               "texlive-latexextra texlive-pictures texlive-mathscience "
               "texlive-fontsrecommended texlive-binextra",
        "tectonic": "sudo pacman -S --needed tectonic",
        "texpkg": "sudo pacman -S --needed {pkgs}",
    },
    "debian": {
        "python3": "sudo apt install python3 python3-venv python3-pip",
        "pdftotext": "sudo apt install poppler-utils",
        "pdftoppm": "sudo apt install poppler-utils",
        "latexmk": "sudo apt install latexmk",
        "tex": "sudo apt install latexmk texlive-latex-base texlive-latex-recommended "
               "texlive-latex-extra texlive-pictures texlive-science texlive-fonts-recommended lmodern",
        "tectonic": None,
        "texpkg": "sudo apt install {pkgs}",
    },
    "fedora": {
        "python3": "sudo dnf install python3",
        "pdftotext": "sudo dnf install poppler-utils",
        "pdftoppm": "sudo dnf install poppler-utils",
        "latexmk": "sudo dnf install latexmk",
        "tex": "sudo dnf install latexmk texlive-scheme-basic texlive-collection-latexrecommended "
               "texlive-collection-latexextra texlive-collection-pictures texlive-collection-mathscience "
               "texlive-collection-fontsrecommended",
        "tectonic": None,
        "texpkg": "sudo dnf install {pkgs}",
    },
    "macos": {
        "python3": "brew install python",
        "pdftotext": "brew install poppler",
        "pdftoppm": "brew install poppler",
        "latexmk": "sudo tlmgr install latexmk",
        "tex": "brew install tectonic   # lightweight; or: brew install --cask basictex",
        "tectonic": "brew install tectonic",
        "texpkg": "sudo tlmgr install {pkgs}",
    },
}
SYS["wsl"] = SYS["debian"]
SYS["unknown"] = {}

# LaTeX package -> distro package (arch, debian) / TeX Live name (tlmgr; Fedora: texlive-<tlmgr>).
TEXPKG = {
    # name:       (arch,                       debian,                      tlmgr)
    "amsmath":   ("texlive-latex",            "texlive-latex-base",        "amsmath"),
    "amssymb":   ("texlive-basic",            "texlive-base",              "amsfonts"),
    "bm":        ("texlive-latex",            "texlive-latex-base",        "tools"),
    "booktabs":  ("texlive-latexrecommended", "texlive-latex-recommended", "booktabs"),
    "enumitem":  ("texlive-latexextra",       "texlive-latex-extra",       "enumitem"),
    "fancyhdr":  ("texlive-latex",            "texlive-latex-base",        "fancyhdr"),
    "float":     ("texlive-latexrecommended", "texlive-latex-recommended", "float"),
    "fontenc":   ("texlive-latex",            "texlive-latex-base",        "latex"),
    "geometry":  ("texlive-latex",            "texlive-latex-base",        "geometry"),
    "graphicx":  ("texlive-latex",            "texlive-latex-base",        "graphics"),
    "hyperref":  ("texlive-latex",            "texlive-latex-base",        "hyperref"),
    "lmodern":   ("texlive-fontsrecommended", "lmodern",                   "lm"),
    "mathtools": ("texlive-latexrecommended", "texlive-latex-recommended", "mathtools"),
    "multicol":  ("texlive-latex",            "texlive-latex-base",        "tools"),
    "multirow":  ("texlive-latexextra",       "texlive-latex-extra",       "multirow"),
    "siunitx":   ("texlive-mathscience",      "texlive-science",           "siunitx"),
    "tabularx":  ("texlive-latex",            "texlive-latex-base",        "tools"),
    "tcolorbox": ("texlive-latexextra",       "texlive-latex-extra",       "tcolorbox"),
    "tikz":      ("texlive-pictures",         "texlive-pictures",          "pgf"),
    "xcolor":    ("texlive-latexrecommended", "texlive-latex-recommended", "xcolor"),
}

PY_REQUIRED = {"yaml": "PyYAML"}
PY_OPTIONAL = {"pint": "Pint", "pytest": "pytest"}


# ---------------------------------------------------------------- detection
def detect_os() -> str:
    uname = os.environ.get("TMINUS_UNAME")
    if uname:
        system, _, release = uname.partition(" ")
    else:
        system, release = platform.system(), platform.release()
    if system == "Darwin":
        return "macos"
    if system == "Windows" or system.startswith(("MINGW", "MSYS", "CYGWIN")):
        return "windows"
    if system != "Linux":
        return "unknown"
    if "microsoft" in release.lower():
        return "wsl"
    path = Path(os.environ.get("TMINUS_OS_RELEASE", "/etc/os-release"))
    info = {}
    if path.is_file():
        for line in path.read_text(errors="replace").splitlines():
            k, _, v = line.partition("=")
            info[k.strip()] = v.strip().strip('"').lower()
    ids = {info.get("ID", "")} | set(info.get("ID_LIKE", "").split())
    if ids & {"arch", "manjaro", "endeavouros"}:
        return "arch"
    if ids & {"debian", "ubuntu"}:
        return "debian"
    if ids & {"fedora", "rhel", "centos"}:
        return "fedora"
    return "unknown"


def which(name: str):
    return shutil.which(name, path=os.environ.get("PATH", ""))


def has_module(mod: str) -> bool:
    fake = {m.strip() for m in os.environ.get("TMINUS_FAKE_MISSING_MODULES", "").split(",") if m.strip()}
    if mod in fake:
        return False
    try:
        return importlib.util.find_spec(mod) is not None
    except (ImportError, ValueError):
        return False


def template_packages(tdir: Path | None = None) -> list[str]:
    tdir = Path(os.environ.get("TMINUS_TEMPLATES_DIR", tdir or ROOT / "templates"))
    pkgs = set()
    pat = re.compile(r"\\(?:usepackage|RequirePackage)\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}")
    for f in sorted(list(tdir.glob("*.tex")) + list(tdir.glob("*.sty"))):
        text = "\n".join(l.split("%", 1)[0] for l in f.read_text(errors="replace").splitlines())
        for m in pat.finditer(text):
            pkgs.update(p.strip() for p in m.group(1).split(",") if p.strip())
    return sorted(pkgs - LOCAL_PACKAGES)


def _version(cmd: list[str]) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        line = (out.stdout or out.stderr).strip().splitlines()
        return line[0][:80] if line else ""
    except (OSError, subprocess.SubprocessError):
        return ""


# ---------------------------------------------------------------- checks
def item(name, tier, ok, detail="", fix=None, status=None):
    return {"name": name, "tier": tier, "status": status or ("OK" if ok else "MISSING"),
            "detail": detail, "fix": fix}


def fix_for(os_class: str, key: str):
    if os_class == "windows":
        return "Use WSL2 (wsl --install), then run /tminus:doctor inside Ubuntu"
    return SYS.get(os_class, {}).get(key)


def tex_pkg_fix(os_class: str, missing: list[str]):
    if not missing:
        return None
    col = {"arch": 0, "debian": 1, "wsl": 1, "macos": 2, "fedora": 2}.get(os_class)
    if col is None:
        return None
    names = sorted({TEXPKG.get(p, (p, p, p))[col] for p in missing})
    if os_class == "fedora":          # Fedora splits TeX Live per CTAN package: texlive-<tlmgr name>
        names = [f"texlive-{n}" for n in names]
    return SYS[os_class]["texpkg"].format(pkgs=" ".join(names))


def run_checks() -> dict:
    os_class = detect_os()
    items = []
    venv = os.environ.get("TMINUS_VENV", str(Path.home() / ".cache" / PLUGIN_NAME / "venv"))
    pip_fix = (f"python3 -m venv {venv} && {venv}/bin/pip install -r {ROOT}/requirements.txt"
               "   # or: /tminus:doctor --install")

    # required
    pyok = sys.version_info >= (3, 9)
    items.append(item("python3 >= 3.9", "required", pyok, platform.python_version(),
                      None if pyok else fix_for(os_class, "python3")))
    for mod, pkg in PY_REQUIRED.items():
        ok = has_module(mod)
        items.append(item(f"python: {pkg}", "required", ok, "", None if ok else pip_fix))
    pymupdf = has_module("pymupdf") or has_module("fitz")
    pdftotext = which("pdftotext")
    ok = bool(pymupdf or pdftotext)
    detail = "PyMuPDF" if pymupdf else ("pdftotext" if pdftotext else "")
    items.append(item("PDF text extractor (PyMuPDF or pdftotext)", "required", ok, detail,
                      None if ok else f"{pip_fix}\n  or: {fix_for(os_class, 'pdftotext')}"))

    # degradable: TeX
    latexmk, pdflatex, tectonic = which("latexmk"), which("pdflatex"), which("tectonic")
    engine = "latexmk" if (latexmk and pdflatex) else ("tectonic" if tectonic else
                                                       ("pdflatex" if pdflatex else None))
    items.append(item("TeX engine (latexmk+pdflatex or tectonic)", "pdf-output", bool(engine),
                      engine or "", None if engine else fix_for(os_class, "tex")))
    missing_pkgs = []
    if engine in ("latexmk", "pdflatex"):
        kpse = which("kpsewhich")
        for p in template_packages():
            found = False
            if kpse:
                r = subprocess.run([kpse, f"{p}.sty"], capture_output=True, text=True)
                found = r.returncode == 0 and bool(r.stdout.strip())
            if not found:
                missing_pkgs.append(p)
        items.append(item("LaTeX packages used by templates", "pdf-output", not missing_pkgs,
                          ("missing: " + ", ".join(missing_pkgs)) if missing_pkgs
                          else f"{len(template_packages())} found",
                          tex_pkg_fix(os_class, missing_pkgs)))
    elif engine == "tectonic":
        items.append(item("LaTeX packages used by templates", "pdf-output", True,
                          "tectonic fetches packages on first build", status="OK"))

    # optional
    ok = bool(which("pdftoppm")) or pymupdf
    items.append(item("page renderer (pdftoppm or PyMuPDF)", "optional", ok,
                      "PyMuPDF" if pymupdf else ("pdftoppm" if ok else ""),
                      None if ok else fix_for(os_class, "pdftoppm")))
    for mod, pkg in PY_OPTIONAL.items():
        ok = has_module(mod)
        items.append(item(f"python: {pkg}", "optional", ok, "", None if ok else pip_fix,
                          status=None if ok else "WARN"))

    req_missing = any(i["tier"] == "required" and i["status"] != "OK" for i in items)
    other_missing = any(i["tier"] != "required" and i["status"] != "OK" for i in items)
    code = 1 if req_missing else (2 if other_missing else 0)
    return {
        "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
        "os_class": os_class, "engine": engine,
        "format_recommended": "pdf" if (engine and not missing_pkgs) else "md",
        "python": sys.executable,
        "tools": {t: which(t) for t in ("latexmk", "pdflatex", "tectonic", "kpsewhich",
                                         "pdftotext", "pdftoppm")},
        "versions": {"python": platform.python_version(),
                     **({engine: _version([which(engine), "--version"])} if engine else {})},
        "items": items, "exit_code": code,
    }


# ---------------------------------------------------------------- output
def render(res: dict) -> str:
    lines = [f"tminus doctor  (OS: {res['os_class']}, engine: {res['engine'] or 'none'}, "
             f"recommended format: {res['format_recommended']})", ""]
    w = max(len(i["name"]) for i in res["items"])
    lines.append(f"{'STATUS':8} {'TIER':11} {'ITEM':{w}}  DETAIL")
    for i in res["items"]:
        lines.append(f"{i['status']:8} {i['tier']:11} {i['name']:{w}}  {i['detail']}")
    fixes = [i for i in res["items"] if i["status"] != "OK" and i["fix"]]
    nofix = [i for i in res["items"] if i["status"] != "OK" and not i["fix"]]
    if fixes:
        lines += ["", "Fix commands (run them yourself; anything with sudo is never run for you):"]
        grouped = {}
        for i in fixes:
            grouped.setdefault(i["fix"], []).append(i["name"])
        for fix, names in grouped.items():
            lines.append(f"- {', '.join(names)}:\n  {fix}")
    if nofix:
        lines += ["", "No known install command for this OS; install manually: "
                  + ", ".join(i["name"] for i in nofix)]
    if res["os_class"] == "windows":
        lines += ["", "Native Windows is best-effort. Recommended: WSL2 with Ubuntu."]
    if not res["engine"]:
        lines += ["", "No TeX engine: every command still works with format: md (Markdown output)."]
    lines += ["", {0: "Result: all good.", 1: "Result: a REQUIRED item is missing.",
                   2: "Result: usable; optional or PDF-output items missing."}[res["exit_code"]]]
    return "\n".join(lines)


def write_cache(res: dict, cache_dir: Path):
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "preflight.json").write_text(json.dumps(res, indent=2))


def fast_check(cache_dir: Path):
    """Return the cached result if fresh and still accurate, else None."""
    f = cache_dir / "preflight.json"
    if not f.is_file():
        return None
    try:
        res = json.loads(f.read_text())
        ts = dt.datetime.fromisoformat(res["timestamp"])
    except (ValueError, KeyError, json.JSONDecodeError):
        return None
    if dt.datetime.now() - ts > CACHE_MAX_AGE:
        return None
    for tool, path in res.get("tools", {}).items():
        if bool(path) != bool(which(tool)):
            return None
    return res


def install(yes: bool) -> int:
    venv = Path(os.environ.get("TMINUS_VENV", Path.home() / ".cache" / PLUGIN_NAME / "venv"))
    steps = [[sys.executable, "-m", "venv", str(venv)],
             [str(venv / "bin" / "pip"), "install", "-q", "-r", str(ROOT / "requirements.txt")]]
    print("Will install Python packages into the plugin venv only (no sudo, nothing global):")
    for s in steps:
        print("  " + " ".join(s))
    if not yes:
        print("Re-run with --install --yes to do it.")
        return 3
    for s in steps:
        if s[1:3] == ["-m", "venv"] and (venv / "bin" / "python").exists():
            continue
        r = subprocess.run(s)
        if r.returncode:
            print(f"FAILED: {' '.join(s)}", file=sys.stderr)
            return r.returncode
    print(f"Done. Scripts now use {venv}/bin/python.")
    return 0


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cache_dir = None
    if "--cache-dir" in argv:
        cache_dir = Path(argv[argv.index("--cache-dir") + 1])
    if "--install" in argv:
        return install("--yes" in argv)
    if "--fast" in argv and cache_dir:
        res = fast_check(cache_dir)
        if res is not None:
            print(f"preflight: cached result from {res['timestamp']} "
                  f"(format {res['format_recommended']}, exit {res['exit_code']})")
            return res["exit_code"]
    res = run_checks()
    if cache_dir:
        write_cache(res, cache_dir)
    print(json.dumps(res, indent=2) if "--json" in argv else render(res))
    return res["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
