#!/usr/bin/env python3
"""Generate the synthetic WM2001 "Widget Mechanics" toy course used by the tminus tests.

Usage: make_toycourse.py [OUTDIR]      (default: tests/fixtures/toycourse/)

Everything here is invented: the subject, the parts (grommets, spindles, flange-lugs,
coil dampers), the text and the numbers. Output is deterministic: text files are
byte-identical across runs and reportlab's invariant mode makes the PDFs reproducible.

The book carries three planted errors (see PLANTED below and tests/fixtures/PLANTED_ERRORS.md)
and slide deck L02 contradicts the book's joint-stiffness method on purpose.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

from reportlab import rl_config

rl_config.invariant = 1

from reportlab.lib.pagesizes import A4, landscape  # noqa: E402
from reportlab.lib.utils import simpleSplit  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

FRONT_PAGES = 6                      # pdf_page = printed_page + FRONT_PAGES
DEFAULT_OUT = Path(__file__).resolve().parent / "toycourse"
PROF = "Prof. A. Example"
PI = math.pi

# Planted book errors: exact string, printed page it sits on, and the truth.
PLANTED = {
    "reversed_limit": {"text": "3 deg/m for precision spindles and 0.25 deg/m for transmission spindles",
                       "printed_page": 8, "correct": "precision 0.25 deg/m, transmission 3 deg/m"},
    "decimal_typo": {"text": "292 / (0.020 x 2000) = 73 C", "printed_page": 21, "correct": "7.3 C"},
    "wrong_answer": {"text": "Ex. 1.1: sigma = 47.7 MPa", "printed_page": 23, "correct": "74.6 MPa"},
}

CHAPTERS = [  # id, title, printed pages, lectures, assignments, self-rating
    ("1", "Grommet Stresses", (1, 6), "L01", "A1", 2),
    ("2", "Spindle Torsion", (7, 12), "L01", "A1, A2", 4),
    ("3", "Flange-lug Joints", (13, 17), "L02", "A2", 3),
    ("4", "Coil Dampers", (18, 22), "L03", "A2", 1),
]


def f(x, nd=1):
    return f"{x:.{nd}f}"


# ----------------------------------------------------------------------------- layout
class Doc:
    """Minimal top-down text layout on a reportlab canvas."""

    def __init__(self, path, title, size=A4, margin=56, footer=None, autobreak=False):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.c = canvas.Canvas(str(path), pagesize=size, invariant=1)
        self.c.setTitle(title)
        self.c.setAuthor("tminus toy course (synthetic)")
        self.c.setCreator("tests/fixtures/make_toycourse.py")
        self.W, self.H = size
        self.m, self.footer, self.autobreak = margin, footer, autobreak
        self.n, self.y = 1, self.H - margin

    def need(self, h):
        if self.y - h < self.m + 14:
            if not self.autobreak:
                raise RuntimeError(f"{self.path.name}: content overflows PDF page {self.n}")
            self.end_page()

    def line(self, s, font="Helvetica", size=10.5, x=0, lead=None):
        lead = lead or size * 1.4
        self.need(lead)
        self.c.setFont(font, size)
        self.c.drawString(self.m + x, self.y - size, s)
        self.y -= lead

    def para(self, s, font="Helvetica", size=10.5, x=0):
        for ln in simpleSplit(s, font, size, self.W - 2 * self.m - x):
            self.line(ln, font, size, x)
        self.y -= size * 0.5

    def center(self, s, font="Helvetica", size=11, lead=None):
        lead = lead or size * 1.6
        self.need(lead)
        self.c.setFont(font, size)
        self.c.drawCentredString(self.W / 2, self.y - size, s)
        self.y -= lead

    def end_page(self):
        txt = self.footer(self.n) if self.footer else None
        if txt:
            self.c.setFont("Helvetica", 9)
            self.c.drawCentredString(self.W / 2, 28, txt)
        self.c.showPage()
        self.n, self.y = self.n + 1, self.H - self.m

    def save(self):
        self.c.save()


def table(doc, caption, rows):
    doc.y -= 4
    doc.line(caption, "Helvetica-Bold", 10.5)
    ncol, rh = len(rows[0]), 17
    w = doc.W - 2 * doc.m
    doc.need(rh * len(rows) + 8)
    top = doc.y
    for i, row in enumerate(rows):
        yb = top - (i + 1) * rh
        doc.c.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 10)
        for j, cell in enumerate(row):
            doc.c.drawString(doc.m + j * w / ncol + 6, yb + 5, cell)
    c = doc.c
    for i in range(len(rows) + 1):
        c.line(doc.m, top - i * rh, doc.m + w, top - i * rh)
    for j in range(ncol + 1):
        c.line(doc.m + j * w / ncol, top, doc.m + j * w / ncol, top - len(rows) * rh)
    doc.y = top - len(rows) * rh - 12


def figure(doc, draw, caption, h=150):
    doc.need(h + 36)
    x, w = doc.m + 20, doc.W - 2 * doc.m - 40
    doc.c.saveState()
    doc.c.setLineWidth(1.2)
    draw(doc.c, x, doc.y - h, w, h)
    doc.c.restoreState()
    doc.y -= h + 8
    doc.center(caption, "Helvetica-Oblique", 10)


def arrow(c, x1, y1, x2, y2):
    c.line(x1, y1, x2, y2)
    a = math.atan2(y2 - y1, x2 - x1)
    for s in (2.6, -2.6):
        c.line(x2, y2, x2 - 9 * math.cos(a + s / 6), y2 - 9 * math.sin(a + s / 6))


def fig_grommet(c, x, y, w, h):
    cx = x + w / 2
    c.rect(cx - 150, y + 50, 300, 20)
    c.rect(cx - 150, y + 70, 300, 20)
    c.rect(cx - 12, y + 25, 24, 95)
    c.rect(cx - 24, y + 120, 48, 10)
    arrow(c, cx - 220, y + 80, cx - 155, y + 80)
    arrow(c, cx + 220, y + 60, cx + 155, y + 60)
    c.setFont("Helvetica", 10)
    c.drawString(cx - 232, y + 76, "F")
    c.drawString(cx + 226, y + 56, "F")
    c.drawString(cx - 4, y + 10, "d")
    c.drawString(cx + 160, y + 92, "t")


def fig_spindle(c, x, y, w, h):
    c.rect(x + 40, y + 15, 14, 120)
    for i in range(8):
        c.line(x + 40, y + 20 + i * 15, x + 28, y + 32 + i * 15)
    c.rect(x + 54, y + 60, 320, 30)
    c.arc(x + 360, y + 40, x + 400, y + 110, -70, 250)
    arrow(c, x + 60, y + 35, x + 370, y + 35)
    c.setFont("Helvetica", 10)
    c.drawString(x + 408, y + 100, "T")
    c.drawString(x + 210, y + 22, "L")
    c.drawString(x + 210, y + 96, "d")


def fig_joint(c, x, y, w, h):
    cx = x + w / 2
    c.rect(cx - 140, y + 75, 280, 22)
    c.rect(cx - 140, y + 53, 280, 22)
    c.rect(cx - 9, y + 35, 18, 80)
    c.rect(cx - 22, y + 97, 44, 14)
    c.rect(cx - 22, y + 39, 44, 14)
    arrow(c, cx + 100, y + 97, cx + 100, y + 140)
    arrow(c, cx + 100, y + 53, cx + 100, y + 10)
    c.setFont("Helvetica", 10)
    c.drawString(cx + 108, y + 128, "P")
    c.drawString(cx + 108, y + 16, "P")
    c.drawString(cx - 160, y + 70, "l")


def fig_damper(c, x, y, w, h):
    x0 = x + 70
    c.rect(x0 + 60, y + 50, 200, 50)
    p = c.beginPath()
    p.moveTo(x0, y + 75)
    for i in range(12):
        p.lineTo(x0 + 30 + i * 25, y + (110 if i % 2 == 0 else 40))
    p.lineTo(x0 + 330, y + 75)
    c.drawPath(p)
    c.setFont("Helvetica", 10)
    c.drawString(x0 + 140, y + 70, "oil")
    c.drawString(x0 + 150, y + 118, "D")


def render(doc, blocks):
    for kind, *a in blocks:
        if kind == "h1":
            doc.line(a[0], "Helvetica-Bold", 18, lead=34)
        elif kind == "h2":
            doc.y -= 4
            doc.line(a[0], "Helvetica-Bold", 12, lead=19)
        elif kind == "p":
            doc.para(a[0])
        elif kind == "eq":
            for s in a[0]:
                doc.line(s, "Courier", 10.5, x=28)
            doc.y -= 5
        elif kind == "ex":
            doc.y -= 4
            doc.line(a[0], "Helvetica-Bold", 11)
            for s in a[1]:
                doc.line(s, "Courier", 9.5, x=14)
            doc.y -= 5
        elif kind == "table":
            table(doc, a[0], a[1])
        elif kind == "fig":
            figure(doc, a[0], a[1])
        else:
            raise ValueError(kind)


# ----------------------------------------------------------------------------- book
def chapter1():
    A1, A_h = PI * 12 ** 2 / 4, PI * (20 ** 2 - 12 ** 2) / 4
    s1 = 9000 / A1
    return [
        [("h1", "Chapter 1  Grommet Stresses"),
         ("p", "A grommet is a short cylindrical pin, solid or hollow, that locates two widget plates "
               "and carries the force between them. This chapter finds the direct stress in the grommet "
               "body and the bearing stress where it presses on its seat plate."),
         ("h2", "1.1 Direct stress"),
         ("p", "For an axial force F acting on a cross-section of area A, the direct stress is uniform:"),
         ("eq", ["sigma = F / A", "solid grommet:  A = pi d^2 / 4", "hollow grommet: A = pi (D^2 - d^2) / 4"]),
         ("p", "Here d is the pin diameter (or bore diameter for a hollow grommet) and D the outer "
               "diameter. Lengths are in mm and forces in N, so stresses come out in MPa.")],
        [("h2", "1.2 Bearing stress"),
         ("p", "Where the grommet presses on a seat plate of thickness t, the contact pressure is taken "
               "over the projected area d t, not the curved area:"),
         ("eq", ["sigma_b = F / (d t)"]),
         ("h2", "1.3 Factor of safety"),
         ("p", "The factor of safety compares the yield strength Sy of the grommet material with the "
               "working stress:"),
         ("eq", ["n = Sy / sigma"]),
         ("table", "Table 1.1 Standard values: grommet materials",
          [["Material", "Sy (MPa)", "E (GPa)", "G (GPa)"], ["G-Brass", "180", "100", "37"],
           ["G-Steel", "300", "200", "80"], ["G-Nylon", "45", "3", "1.1"]])],
        [("fig", fig_grommet, "Fig. 1.1 Grommet pin seated in two plates"),
         ("p", "Figure 1.1 shows the load path: the force F enters through the upper plate, crosses "
               "the grommet at the joint plane, and leaves through the lower plate. The grommet body "
               "carries the direct stress; each plate edge carries the bearing stress.")],
        [("ex", "Worked Example 1.1", [
            "A solid G-Steel grommet, d = 12 mm, carries F = 9 kN. Find sigma and n.",
            f"A = pi x 12^2 / 4 = {f(A1)} mm^2",
            f"sigma = 9000 / {f(A1)} = {f(s1)} MPa",
            f"n = 300 / {f(s1)} = {f(300 / s1, 2)}"]),
         ("p", "The factor of safety is comfortable; a G-Nylon grommet of the same size would yield.")],
        [("ex", "Worked Example 1.2", [
            "A G-Brass grommet, d = 10 mm, sits in a seat plate t = 8 mm and carries F = 6 kN.",
            "Find the bearing stress and the factor of safety.",
            "sigma_b = 6000 / (10 x 8) = 75.0 MPa",
            "n = 180 / 75.0 = 2.40"])],
        [("h2", "Exercises"),
         ("p", "Exercise 1.1  A hollow grommet has D = 20 mm and bore d = 12 mm and carries F = 15 kN. "
               "Find the direct stress."),
         ("p", "Exercise 1.2  A grommet pin of d = 8 mm bears on a seat plate t = 6 mm and carries "
               "4.8 kN. Find the bearing stress."),
         ("p", f"(Check value for Exercise 1.1: the load-carrying area is {f(A_h)} mm^2.)")],
    ]


def chapter2():
    tau1 = 16 * 150e3 / (PI * 30 ** 3)
    th = 0.25 / 1000 * PI / 180
    J = 40e3 / (80e3 * th)
    d_req = (32 * J / PI) ** 0.25
    d_tr = (32 * (J / 12) / PI) ** 0.25
    return [
        [("h1", "Chapter 2  Spindle Torsion"),
         ("p", "A spindle is a solid round shaft that turns a widget head. It must be strong enough "
               "not to yield in shear and stiff enough not to twist too far along its length."),
         ("h2", "2.1 Torsional shear stress"),
         ("p", "A torque T (N mm) on a solid spindle of diameter d (mm) gives a peak surface shear stress"),
         ("eq", ["tau = 16 T / (pi d^3)"])],
        [("h2", "2.2 Angle of twist"),
         ("p", "Over a length L the spindle twists through an angle (in radians)"),
         ("eq", ["theta = T L / (G J),   J = pi d^4 / 32",
                 "twist per metre (deg/m) = T / (G J) x (180 / pi) x 1000"]),
         ("h2", "2.3 Allowable twist"),
         ("p", "Standard values. Allowable spindle twist is 3 deg/m for precision spindles and "
               "0.25 deg/m for transmission spindles. Spindle steel (G-Steel) has G = 80 GPa."),
         ("p", "Twist, not strength, usually decides the diameter of a long spindle.")],
        [("fig", fig_spindle, "Fig. 2.1 Spindle fixed at one end with torque T at the other"),
         ("p", "In Figure 2.1 the left end is held by the frame; the free end turns through theta.")],
        [("ex", "Worked Example 2.1", [
            "A spindle of d = 30 mm transmits T = 150 N m. Find the shear stress.",
            f"tau = 16 x 150 000 / (pi x 30^3) = {f(tau1)} MPa"])],
        [("ex", "Worked Example 2.2", [
            "A precision spindle carries T = 40 N m; G = 80 GPa. Precision spindles are",
            "limited to 0.25 deg/m. Find the smallest diameter.",
            f"theta/L = 0.25 / 1000 x pi / 180 = {th:.4e} rad/mm",
            f"J = T / (G theta/L) = 40 000 / (80 000 x {th:.4e}) = {J:.0f} mm^4",
            f"d = (32 J / pi)^(1/4) = {f(d_req)} mm  ->  use d = 34 mm",
            f"(A transmission spindle, allowed 3 deg/m, would need only d = {f(d_tr)} mm.)"])],
        [("h2", "Exercises"),
         ("p", "Exercise 2.1  A spindle of d = 30 mm transmits 112 N m. Find the shear stress."),
         ("p", "Exercise 2.2  A transmission spindle of d = 25 mm carries T = 60 N m; G = 80 GPa. "
               "Find the twist per metre and check it against the transmission limit of 3 deg/m.")],
    ]


def chapter3():
    An = PI * 12 ** 2 / 4
    kb = An * 200e3 / 40 / 1000
    C = round(kb / (kb + 1400), 3)
    return [
        [("h1", "Chapter 3  Flange-lug Joints"),
         ("p", "A flange-lug joint clamps two flanges with a lug bolt tightened to a preload Fi. "
               "When an external load P pulls the flanges apart, the bolt takes only a share of it."),
         ("h2", "3.1 Stiffnesses"),
         ("p", "The lug bolt acts as a spring of stiffness kb over its grip length l, and the clamped "
               "flanges as a spring of stiffness km. This book takes A as the nominal shank area:"),
         ("eq", ["kb = A E / l,   A = pi d^2 / 4"]),
         ("h2", "3.2 Joint stiffness ratio"),
         ("eq", ["C = kb / (kb + km)", "Fb = Fi + C P"]),
         ("p", "C is the fraction of the external load that reaches the bolt.")],
        [("table", "Table 3.1 Standard values: lug bolt sizes",
          [["Size", "d (mm)", "Nominal A (mm^2)", "Stress area A_t (mm^2)"],
           ["LB8", "8", "50.3", "36.6"], ["LB10", "10", "78.5", "58.0"],
           ["LB12", "12", "113.1", "84.3"], ["LB16", "16", "201.1", "157.0"]]),
         ("p", "E = 200 GPa for all lug bolts.")],
        [("fig", fig_joint, "Fig. 3.1 Flange-lug joint under separating load P"),
         ("ex", "Worked Example 3.1", [
             "An LB12 lug bolt, grip l = 40 mm, E = 200 GPa, clamps flanges with",
             "km = 1400 kN/mm. Find the joint stiffness ratio C.",
             f"A = pi x 12^2 / 4 = {f(An)} mm^2",
             f"kb = {f(An)} x 200 000 / 40 = {f(kb)} kN/mm",
             f"C = {f(kb)} / ({f(kb)} + 1400) = {C:.3f}"])],
        [("ex", "Worked Example 3.2", [
            "The joint of Example 3.1 has preload Fi = 20 kN and external load P = 10 kN.",
            "Find the resultant bolt load.",
            f"Fb = 20 + {C:.3f} x 10 = {f(20 + C * 10, 2)} kN"])],
        [("h2", "Exercises"),
         ("p", "Exercise 3.1  An LB10 lug bolt (nominal area), grip l = 30 mm, E = 200 GPa, clamps "
               "flanges with km = 1000 kN/mm. Find C."),
         ("p", "Exercise 3.2  A joint has Fi = 15 kN, P = 8 kN and C = 0.25. Find Fb.")],
    ]


def chapter4():
    k = 80e3 * 4 ** 4 / (8 * 32 ** 3 * 8)
    return [
        [("h1", "Chapter 4  Coil Dampers"),
         ("p", "A coil damper is a helical coil wrapped round a small oil cylinder. The coil returns "
               "the widget carriage; the oil turns the carriage's kinetic energy into heat."),
         ("h2", "4.1 Coil rate"),
         ("eq", ["k = G d^4 / (8 D^3 N)"]),
         ("p", "d is the wire diameter, D the mean coil diameter and N the number of active turns."),
         ("h2", "4.2 Energy and temperature rise"),
         ("eq", ["E = 1/2 m v^2", "dT = E / (m_oil c_oil)"]),
         ("p", "Standard value: damper oil has c_oil = 2000 J/(kg K).")],
        [("fig", fig_damper, "Fig. 4.1 Coil damper around its oil cylinder"),
         ("p", "The oil cylinder in Figure 4.1 holds only a few grams of oil, so it warms quickly.")],
        [("ex", "Worked Example 4.1", [
            "A coil damper has G = 80 GPa, d = 4 mm, D = 32 mm and N = 8. Find the rate.",
            f"k = 80 000 x 4^4 / (8 x 32^3 x 8) = {f(k, 2)} N/mm"])],
        [("ex", "Worked Example 4.2", [
            "A 146 kg widget carriage moving at 2.0 m/s is stopped by a coil damper holding",
            "0.020 kg of oil (c_oil = 2000 J/(kg K)). Find the oil temperature rise.",
            "E = 0.5 x 146 x 2.0^2 = 292 J",
            "dT = 292 / (0.020 x 2000) = 73 C"])],     # planted: correct is 7.3 C
        [("h2", "Exercises"),
         ("p", "Exercise 4.1  A coil damper has G = 80 GPa, d = 5 mm, D = 40 mm and N = 6. Find k."),
         ("p", "Exercise 4.2  A 90 kg carriage at 3.0 m/s is stopped by a damper holding 0.030 kg "
               "of oil (c_oil = 2000 J/(kg K)). Find the temperature rise.")],
    ]


def answers():
    tau = 16 * 112e3 / (PI * 30 ** 3)
    J = PI * 25 ** 4 / 32
    tw = 60e3 / (80e3 * J) * 180 / PI * 1000
    kb = PI * 10 ** 2 / 4 * 200e3 / 30 / 1000
    k = 80e3 * 5 ** 4 / (8 * 40 ** 3 * 6)
    dT = 0.5 * 90 * 3.0 ** 2 / (0.030 * 2000)
    return [("h1", "Answers to Exercises"),
            ("eq", ["Ex. 1.1: sigma = 47.7 MPa",          # planted: correct is 74.6 MPa
                    "Ex. 1.2: sigma_b = 100.0 MPa",
                    f"Ex. 2.1: tau = {f(tau)} MPa",
                    f"Ex. 2.2: {f(tw, 2)} deg/m (within the 3 deg/m transmission limit)",
                    f"Ex. 3.1: C = {kb / (kb + 1000):.3f}",
                    f"Ex. 3.2: Fb = {f(15 + 0.25 * 8)} kN",
                    f"Ex. 4.1: k = {f(k)} N/mm",
                    f"Ex. 4.2: dT = {f(dT)} C"])]


FRONT = [
    [("h1", "WIDGET MECHANICS"), ("p", "A First Course for WM2001"),
     ("p", "Synthetic text written for software testing. Every name, part, value and formula "
           "in this book is fictional."), ("p", "Toy Press, 2026")],
    [("p", "This synthetic book may be copied and reused freely. It describes no real machine.")],
    [("h2", "Preface"),
     ("p", "Widget Mechanics covers four parts found in every widget: grommets, spindles, "
           "flange-lug joints and coil dampers. Each chapter gives the theory, two worked examples "
           "and two exercises; answers are at the back.")],
    [("h2", "Contents"),
     ("eq", ["Chapter 1  Grommet Stresses ............. 1", "Chapter 2  Spindle Torsion .............. 7",
             "Chapter 3  Flange-lug Joints ............ 13", "Chapter 4  Coil Dampers ................ 18",
             "Answers to Exercises ................... 23", "Index .................................. 24"])],
    [("h2", "List of Symbols"),
     ("eq", ["F, P   force (N)", "sigma  direct stress (MPa)", "tau    shear stress (MPa)",
             "T      torque (N mm)", "C      joint stiffness ratio", "k      coil rate (N/mm)",
             "dT     temperature rise (C)"])],
    [("h2", "To the Student"),
     ("p", "Work in mm, N and MPa throughout. Read each worked example with a calculator in hand.")],
]

INDEX = [("h1", "Index"),
         ("eq", ["allowable twist .......... 8", "bearing stress ........... 2", "coil rate ................ 18",
                 "factor of safety ......... 2", "joint stiffness ratio .... 13", "lug bolt sizes ........... 14",
                 "temperature rise ......... 18"])]


def make_book(out):
    body = chapter1() + chapter2() + chapter3() + chapter4() + [answers(), INDEX]
    doc = Doc(out / "book.pdf", "Widget Mechanics",
              footer=lambda n: str(n - FRONT_PAGES) if n > FRONT_PAGES else None)
    for page in FRONT + body:
        render(doc, page)
        doc.end_page()
    doc.save()
    return len(FRONT) + len(body)


# ----------------------------------------------------------------------------- slides
SLIDES = {
    "L01": ("Lecture 1: Grommet Stresses and Spindle Torsion", "Book chapters 1 and 2", [
        ("Grommet stresses", ["Direct stress sigma = F / A", "Hollow grommet: A = pi (D^2 - d^2) / 4",
                              "Bearing stress on the seat: sigma_b = F / (d t)", "Factor of safety n = Sy / sigma"]),
        ("Quick example", ["G-Steel grommet, d = 12 mm, F = 9 kN", "A = 113.1 mm^2, sigma = 79.6 MPa",
                           "n = 300 / 79.6 = 3.77"]),
        ("Spindle torsion", ["tau = 16 T / (pi d^3)", "theta = T L / (G J),  J = pi d^4 / 32",
                             "Long spindles: stiffness decides d, not strength"]),
        ("Twist limits", ["Precision spindles: 0.25 deg/m (they must stay stiff)",
                          "Transmission spindles: 3 deg/m", "G = 80 GPa for spindle steel"]),
    ]),
    "L02": ("Lecture 2: Flange-lug Joints", "Book chapter 3", [
        ("Joint model", ["Bolt spring kb, flange spring km", "C = kb / (kb + km)", "Fb = Fi + C P"]),
        ("Convention for this course", ["For kb, use stress area A_t, not nominal area",
                                        "kb = A_t E / l   (A_t from Table 3.1)",
                                        "The book uses pi d^2 / 4: answers using it lose marks here"]),
        ("Worked example (redo of book Ex. 3.1 and 3.2)", [
            "LB12: A_t = 84.3 mm^2, l = 40 mm, E = 200 GPa, km = 1400 kN/mm",
            "kb = 84.3 x 200 000 / 40 = 421.5 kN/mm", "C = 421.5 / (421.5 + 1400) = 0.231",
            "Fi = 20 kN, P = 10 kN:  Fb = 20 + 0.231 x 10 = 22.31 kN",
            "(The book gets C = 0.288 and Fb = 22.88 kN with nominal area.)"]),
        ("Summary", ["Stiffer flanges -> smaller C -> bolt sees less of P", "Always quote A_t in your answer"]),
    ]),
    "L03": ("Lecture 3: Coil Dampers", "Book chapter 4", [
        ("Coil rate", ["k = G d^4 / (8 D^3 N)", "Halve d -> rate falls 16 times"]),
        ("Temperature rise", ["IMPORTANT for exam: damper temperature rise",
                              "E = 1/2 m v^2,  dT = E / (m_oil c_oil)", "c_oil = 2000 J/(kg K)",
                              "This formula is not printed in the paper"]),
        ("Example", ["100 kg at 2.0 m/s, 0.025 kg of oil", "E = 0.5 x 100 x 2.0^2 = 200 J",
                     "dT = 200 / (0.025 x 2000) = 4.0 C"]),
        ("Summary", ["Coil returns the carriage; oil absorbs the energy", "Check units: J, kg, J/(kg K)"]),
    ]),
}


def make_slides(out):
    for code, (title, maps, slides) in SLIDES.items():
        n_total = len(slides) + 1
        doc = Doc(out / "slides" / f"{code}.pdf", title, size=landscape(A4), margin=50,
                  footer=lambda n, code=code: f"WM2001 Widget Mechanics  |  {PROF}  |  {code} slide {n}")
        doc.y -= 120
        doc.center("WM2001 Widget Mechanics", "Helvetica-Bold", 28, 44)
        doc.center(title, "Helvetica", 20, 34)
        doc.center(PROF, "Helvetica", 16, 28)
        doc.center(maps, "Helvetica-Oblique", 14)
        doc.end_page()
        for head, bullets in slides:
            doc.line(head, "Helvetica-Bold", 26, lead=46)
            for b in bullets:
                doc.para("- " + b, "Helvetica", 18)
            doc.end_page()
        doc.save()
        assert doc.n - 1 == n_total


# ----------------------------------------------------------------------------- assignments
ASSIGNMENTS = {
    "A1": [
        "A hollow G-Steel grommet has D = 24 mm and bore d = 14 mm and carries F = 20 kN. "
        "Find the direct stress and the factor of safety.",
        "A G-Brass grommet pin of d = 10 mm carries 5 kN. Find the seat-plate thickness t that "
        "keeps the bearing stress below 60 MPa.",
        "A spindle of d = 28 mm transmits 120 N m. Find the torsional shear stress.",
    ],
    "A2": [
        "A precision spindle 0.8 m long carries T = 30 N m, G = 80 GPa. Find the smallest diameter "
        "that meets the allowable twist for precision spindles.",
        "An LB16 lug bolt with grip l = 50 mm clamps flanges with km = 2000 kN/mm. With Fi = 30 kN "
        "and P = 15 kN, find C and Fb.",
        "A 120 kg carriage at 2.5 m/s is stopped by a coil damper holding 0.040 kg of oil. "
        "Find the oil temperature rise.",
    ],
}


def make_assignments(out):
    for code, problems in ASSIGNMENTS.items():
        doc = Doc(out / "assignments" / f"{code}.pdf", f"WM2001 Assignment {code}", autobreak=True)
        doc.center(f"WM2001 Widget Mechanics - Assignment {code}", "Helvetica-Bold", 15)
        doc.center(PROF, "Helvetica", 11, 30)
        for i, p in enumerate(problems, 1):
            doc.para(f"Problem {i}. {p}")
        doc.end_page()
        doc.save()


# ----------------------------------------------------------------------------- past papers
# Each question: (id, chapter, marks, text). Q1 parts are one-liners with bracketed options.
PAPERS = {
    "2023": [
        ("Q1a", "1", 2, "Bearing stress on a grommet seat uses the [projected area d t / full pin area pi d^2/4]."),
        ("Q1b", "1", 2, "The load-carrying area of a hollow grommet is [pi D^2/4 / pi (D^2 - d^2)/4]."),
        ("Q1c", "2", 2, "Doubling a spindle's diameter divides its torsional shear stress by [2 / 8]."),
        ("Q1d", "3", 2, "Raising the flange stiffness km makes the joint stiffness ratio C [larger / smaller]."),
        ("Q1e", "4", 2, "Halving the wire diameter of a coil damper divides its rate by [4 / 16]."),
        ("Q2", "1", 14, "A hollow G-Brass grommet (D = 30 mm, bore d = 18 mm) carries F = 40 kN through a "
                        "seat plate t = 10 mm. Find (i) the direct stress, (ii) the factor of safety, "
                        "(iii) the bearing stress on the seat plate."),
        ("Q3", "2", 14, "A transmission spindle 1.2 m long transmits T = 500 N m; G = 80 GPa and the "
                        "allowable shear stress is 40 MPa. Find the smallest diameter that satisfies both "
                        "strength and the allowable twist. Use: tau = 16T/(pi d^3); theta = T L/(G J), "
                        "J = pi d^4/32."),
        ("Q4", "3", 12, "An LB10 lug bolt (A_t = 58.0 mm^2), grip l = 30 mm, E = 200 GPa, clamps flanges "
                        "with km = 900 kN/mm. With Fi = 12 kN and P = 6 kN find C and the resultant bolt "
                        "load. Use: Fb = Fi + C P."),
    ],
    "2024": [
        ("Q1a", "2", 2, "Allowable twist for a precision spindle is [0.25 / 3] deg/m."),
        ("Q1b", "3", 2, "For lug-bolt stiffness this course uses the [nominal area / stress area A_t]."),
        ("Q1c", "3", 2, "The resultant bolt load is [Fi + C P / Fi + (1 - C) P]."),
        ("Q1d", "4", 2, "Temperature rise of a coil damper is [E/(m c) / m c/E]."),
        ("Q1e", "4", 2, "Coil rate varies with the mean coil diameter D as [1/D^3 / 1/D]."),
        ("Q2", "2", 12, "A spindle of d = 32 mm carries T = 250 N m; G = 80 GPa. Find the shear stress and "
                        "the twist per metre. Can it serve as a precision spindle? Use: tau = 16T/(pi d^3)."),
        ("Q3", "3", 14, "An LB12 lug bolt (A_t = 84.3 mm^2), grip l = 50 mm, E = 200 GPa, clamps flanges "
                        "with km = 1100 kN/mm. With Fi = 25 kN and P = 12 kN find C and Fb. "
                        "Use: C = kb/(kb + km), kb = A_t E / l."),
        ("Q4", "4", 14, "A coil damper has G = 80 GPa, d = 6 mm, D = 48 mm, N = 7. (i) Find its rate. "
                        "(ii) It stops a 200 kg carriage moving at 1.5 m/s and holds 0.040 kg of oil. "
                        "Find the oil temperature rise. Use: k = G d^4/(8 D^3 N)."),
    ],
}
PAPER_TOTAL = 50


def make_papers(out):
    marks = {}
    for year, qs in PAPERS.items():
        marks[year] = {q: {"chapter": ch, "marks": m} for q, ch, m, _ in qs}
        assert sum(m for _, _, m, _ in qs) == PAPER_TOTAL, year
        doc = Doc(out / "papers" / f"{year}.pdf", f"WM2001 End-Semester {year}", autobreak=True)
        doc.center(f"WM2001 Widget Mechanics - End-Semester Examination {year}", "Helvetica-Bold", 14)
        doc.center(f"Examiner: {PROF}    Time: 2 hours    Maximum marks: {PAPER_TOTAL}", "Helvetica", 10.5)
        doc.center("Answer all questions. Take G = 80 GPa and E = 200 GPa unless stated.", "Helvetica", 10.5, 30)
        q1 = [q for q in qs if q[0].startswith("Q1")]
        doc.para(f"Q1. Choose the correct option in each bracket ({len(q1)} x 2 = "
                 f"{sum(m for *_, m, _ in q1)} marks).", "Helvetica-Bold")
        for q, _, m, text in q1:
            doc.para(f"({q[-1]}) {text} [{m} marks]", x=18)
        for q, _, m, text in qs[len(q1):]:
            doc.y -= 4
            doc.para(f"{q}. [{m} marks]", "Helvetica-Bold")
            body, _, given = text.partition(" Use: ")
            doc.para(body, x=18)
            if given:
                doc.line("Use: " + given, "Courier", 10, x=18)
        doc.end_page()
        doc.save()
    (out / "papers" / "marks.json").write_text(json.dumps(marks, indent=2, sort_keys=True) + "\n")
    return marks


# ----------------------------------------------------------------------------- course.md
def past_paper_cell(cid):
    parts = [f"{year} {q} ({m})" for year in sorted(PAPERS, reverse=True)
             for q, ch, m, _ in PAPERS[year] if ch == cid]
    return "; ".join(parts) if parts else "-"


def course_md():
    rows = "\n".join(f"| {cid} | {title} | {a}-{b} | {lec} | {asg} | {past_paper_cell(cid)} | {rating} |"
                     for cid, title, (a, b), lec, asg, rating in CHAPTERS)
    return f"""---
course_code: WM2001
course_name: Widget Mechanics
schema_version: 2
exam_datetime: 2026-12-01T09:00
hours_per_day: 6
book_policy: closed
format: pdf
exam_pattern: |
  Q1: five one-liners with bracketed options, 2 marks each (10 marks).
  Q2-Q4: numericals of 12-14 marks; key formulas are printed inside the question.
  Answer all questions; 2 hours; {PAPER_TOTAL} marks.
paper_total: {PAPER_TOTAL}
---

## Book
- path: book.pdf
- page_offset: {FRONT_PAGES}

## Chapters
| id | title | book pages (printed) | lectures | assignments | past papers | self-rating (1-5) |
|----|-------|----------------------|----------|-------------|-------------|--------------------|
{rows}

## Professor conventions (OVERRIDE THE BOOK)
- Joint stiffness ratio C | uses the stress area A_t, not the nominal area pi d^2/4, in kb = A_t E / l (book Ex. 3.1 gets C = 0.288, the professor C = 0.231; Fb 22.88 vs 22.31 kN) | slides/L02.pdf slide 3-4 | 2026-11-22

## Given vs must-remember formulas
### Given in the paper
- tau = 16T/(pi d^3)  (2023 Q3, 2024 Q2)
- theta = T L/(G J), J = pi d^4/32  (2023 Q3)
- Fb = Fi + C P  (2023 Q4)
- C = kb/(kb + km), kb = A_t E / l  (2024 Q3)
- k = G d^4/(8 D^3 N)  (2024 Q4)
### Must remember
- sigma = F/A; hollow grommet A = pi (D^2 - d^2)/4
- sigma_b = F/(d t); n = Sy/sigma
- allowable twist: precision 0.25 deg/m, transmission 3 deg/m
- E = 1/2 m v^2; dT = E/(m_oil c_oil), c_oil = 2000 J/(kg K)

## Verified corrections log
| date | location | book/slide says | correct value | how verified |
|------|----------|-----------------|---------------|--------------|
"""


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    out = Path(argv[0]) if argv else DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    pages = make_book(out)
    make_slides(out)
    make_assignments(out)
    make_papers(out)
    (out / "course.expected.md").write_text(course_md())
    print(f"toy course written to {out} (book: {pages} pages, offset {FRONT_PAGES})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
