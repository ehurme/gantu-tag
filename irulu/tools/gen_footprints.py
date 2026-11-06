"""Generate the project footprint library (<project>.pretty) and simple 3D models (<project>.3dshapes).

Shared by the three v8 designs (battery, solar, sensor); each design uses the subset it needs.
Derived from v7's generator. Land patterns:
  InPlay_IN100_QFN-18-1EP_3x3mm_P0.4mm_EP1.5x1.7mm  IN100-Q1-R-RC1I (same pads as v7)
  Crystal_SMD_1612-4Pin_1.6x1.2mm                    TXC 8Q26000008
  C_0402 / R_0402 / C_0805                           KiCad land patterns
  D_SOD-523                                          KiCad land pattern (RB751S40)
  PD_0805_TEMD7000                                   KiCad LED_0805 land pattern (pad 1 = cathode)
  SOT-23-3                                           KiCad SOT-23 land pattern (TPS3839DBZ)
  SOT-363_SC-70-6                                    KiCad land pattern (Si1553CDL)
  LGA-12_2x2mm_P0.5mm                                KiCad land pattern (LSM303AGR, same as LIS2MDL)
  Bosch_LGA-10_2x2mm_P0.5mm_BMP581                   pad positions from SparkFun's BMP581 board, enlarged slightly
  Seeed_XIAO_nRF52840_SMD                            Seeed's official SMD land pattern (OPL KiCad library), bottom pads included
  Antenna_WirePad_THT_D1.1mm_Drill0.6mm              plated hole for the wire antenna
  ProgPads_2x02_P2.54mm_D1.6mm_THT_Tab               programming pads on the cut-off tail
  Cell_Button_NegPad2mm_PlusEdge                     D1 cell interface (bottom - pad, + pads both sides)
  SolderJumper_OFF_Tail, KiKit_Tab_*                 as v7
  BatteryPads_LiPo_2x3mm                             D3 LiPo pads
"""
import math
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D  # noqa: E402

LIB = getattr(D, "LIB", "insect_tag")
OUT = os.path.join(HERE, "..", LIB + ".pretty")
OUT3D = os.path.join(HERE, "..", LIB + ".3dshapes")
MODEL = "${KIPRJMOD}/" + LIB + ".3dshapes/%s.wrl"


def u():
    return str(uuid.uuid4())


# ------------------------------------------------------------------ footprint primitives
def txt(kind, text, x, y, layer, size=0.5, thick=0.08, hide=False, mirror=False):
    h = " hide" if hide else ""
    j = " (justify mirror)" if mirror else ""
    return (f'  (fp_text {kind} "{text}" (at {x} {y}) (layer "{layer}"){h}\n'
            f'    (effects (font (size {size} {size}) (thickness {thick})){j})\n'
            f'    (tstamp {u()})\n  )\n')


def line(x1, y1, x2, y2, layer, w=0.1):
    return (f'  (fp_line (start {round(x1, 4)} {round(y1, 4)}) (end {round(x2, 4)} {round(y2, 4)}) '
            f'(stroke (width {w}) (type solid)) (layer "{layer}") (tstamp {u()}))\n')


def rect(x1, y1, x2, y2, layer, w=0.05):
    return (line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) +
            line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w))


def circle(cx, cy, r, layer, w=0.1):
    return (f'  (fp_circle (center {cx} {cy}) (end {round(cx + r, 4)} {cy}) (stroke (width {w}) (type solid)) '
            f'(fill none) (layer "{layer}") (tstamp {u()}))\n')


def smd(num, x, y, w, h, shape="roundrect", layers='"F.Cu" "F.Paste" "F.Mask"', rr=0.25, rot=0, extra=""):
    rrs = f" (roundrect_rratio {rr})" if shape == "roundrect" else ""
    r = f" {rot}" if rot else ""
    return (f'  (pad "{num}" smd {shape} (at {round(x, 4)} {round(y, 4)}{r}) (size {w} {h}) (layers {layers}){rrs}{extra} '
            f'(tstamp {u()}))\n')


def tht(num, x, y, d, drill, shape="circle"):
    return (f'  (pad "{num}" thru_hole {shape} (at {round(x, 4)} {round(y, 4)}) (size {d} {d}) (drill {drill}) '
            f'(layers "*.Cu" "*.Mask") (tstamp {u()}))\n')


def model(name, z=0.0):
    return (f'  (model "{MODEL % name}"\n    (offset (xyz 0 0 {z}))\n    (scale (xyz 1 1 1))\n'
            f'    (rotate (xyz 0 0 0))\n  )\n')


def footprint(name, body, descr, tags, attr):
    return (f'(footprint "{name}" (version 20221018) (generator pcbnew)\n'
            f'  (layer "F.Cu")\n  (descr "{descr}")\n  (tags "{tags}")\n'
            f'  (attr {attr})\n{body})\n')


def write(name, text):
    with open(os.path.join(OUT, name + ".kicad_mod"), "w") as f:
        f.write(text)


# ------------------------------------------------------------------ VRML (mm in, 0.1 inch out; y flipped to model space)
S = 1 / 2.54
COL = {"body": (0.08, 0.08, 0.09), "metal": (0.82, 0.82, 0.84), "tin": (0.75, 0.75, 0.76),
       "ceramic": (0.86, 0.80, 0.66), "cap": (0.62, 0.48, 0.32), "mark": (0.9, 0.9, 0.9),
       "cell": (0.78, 0.79, 0.82), "copper": (0.80, 0.45, 0.20), "kapton": (0.9, 0.55, 0.1),
       "clear": (0.55, 0.62, 0.75), "pcb": (0.10, 0.25, 0.55), "lga": (0.85, 0.85, 0.80)}


def mesh_box(x0, y0, z0, x1, y1, z1):
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    f = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    return v, f


def mesh_cyl(cx, cy, z0, z1, r, n=40, axis="z"):
    v, f = [], []
    for i in range(n):
        a = 2 * math.pi * i / n
        if axis == "z":
            v += [(cx + r * math.cos(a), cy + r * math.sin(a), z0), (cx + r * math.cos(a), cy + r * math.sin(a), z1)]
        else:
            v += [(cx, cy + r * math.cos(a), z0 + r * math.sin(a)), (cx + z1, cy + r * math.cos(a), z0 + r * math.sin(a))]
    for i in range(n):
        j = (i + 1) % n
        f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    f.append(tuple(2 * i for i in range(n))[::-1])
    f.append(tuple(2 * i + 1 for i in range(n)))
    return v, f


def wrl(name, parts):
    out = ["#VRML V2.0 utf8", f"# {name}: generated by tools/gen_footprints.py"]
    for key, (v, f) in parts:
        r, g, b = COL[key]
        pts = ", ".join(f"{x * S:.5f} {-y * S:.5f} {z * S:.5f}" for x, y, z in v)
        idx = ", ".join(" ".join(str(i) for i in face) + " -1, " + " ".join(str(i) for i in face[::-1]) + " -1"
                        for face in f)
        out.append(f"Shape {{ appearance Appearance {{ material Material {{ diffuseColor {r} {g} {b} "
                   f"specularColor 0.3 0.3 0.3 shininess 0.4 }} }}\n"
                   f"  geometry IndexedFaceSet {{ solid FALSE coord Coordinate {{ point [ {pts} ] }}\n"
                   f"    coordIndex [ {idx} ] }} }}")
    os.makedirs(OUT3D, exist_ok=True)
    with open(os.path.join(OUT3D, name + ".wrl"), "w") as fh:
        fh.write("\n".join(out) + "\n")


def two_terminal_model(name, L, W, H, body="cap", term=0.25):
    wrl(name, [(body, mesh_box(-L / 2 + term, -W / 2, 0.0, L / 2 - term, W / 2, H)),
               ("tin", mesh_box(-L / 2, -W / 2, 0.0, -L / 2 + term, W / 2, H)),
               ("tin", mesh_box(L / 2 - term, -W / 2, 0.0, L / 2, W / 2, H))])


def courtyard_from_pads(pads, margin=0.15):
    xs, ys = [], []
    for _, x, y, w, h in pads:
        xs += [x - w / 2, x + w / 2]
        ys += [y - h / 2, y + h / 2]
    return min(xs) - margin, min(ys) - margin, max(xs) + margin, max(ys) + margin


# ------------------------------------------------------------------ IN100 QFN18 (unchanged from v7)
QFN_PADS = []
for i in range(7):
    QFN_PADS.append((str(1 + i), -1.4, -1.2 + 0.4 * i, 0.7, 0.2))
QFN_PADS += [("8", -0.25, 1.4, 0.25, 0.7), ("9", 0.25, 1.4, 0.25, 0.7)]
for i in range(7):
    QFN_PADS.append((str(10 + i), 1.4, 1.2 - 0.4 * i, 0.7, 0.2))
QFN_PADS += [("17", 0.25, -1.4, 0.25, 0.7), ("18", -0.25, -1.4, 0.25, 0.7)]


def in100_qfn18():
    name = "InPlay_IN100_QFN-18-1EP_3x3mm_P0.4mm_EP1.5x1.7mm"
    b = txt("reference", "REF**", 0, -2.3, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, 2.3, "F.Fab", 0.3, 0.05, hide=True)
    for num, x, y, w, h in QFN_PADS:
        b += smd(num, x, y, w, h, rr=0.2)
    b += smd("19", 0, 0, 1.5, 1.7, "rect", '"F.Cu" "F.Mask"')
    # v8.3: EP paste as a cross through the centre, clear of the four thermal vias at (+-0.4, +-0.45): every
    # aperture edge is >= 0.13 mm from a 0.3 mm via drill (v8.2's four windows sat right over the vias, so the
    # barrels could swallow the paste). ~28 % coverage.
    b += smd("", 0, 0, 1.3, 0.34, "rect", '"F.Paste"')
    b += smd("", 0, 0, 0.24, 1.5, "rect", '"F.Paste"')
    b += rect(-1.5, -1.5, 1.5, 1.5, "F.Fab", 0.08)
    b += line(-1.5, -0.9, -0.9, -1.5, "F.Fab", 0.08)
    cy = [(-1.52, -1.52), (-0.43, -1.52), (-0.43, -1.8), (0.43, -1.8), (0.43, -1.52), (1.52, -1.52), (1.52, -1.35),
          (1.8, -1.35), (1.8, 1.35), (1.52, 1.35), (1.52, 1.52), (0.43, 1.52), (0.43, 1.8), (-0.43, 1.8),
          (-0.43, 1.52), (-1.52, 1.52), (-1.52, 1.35), (-1.8, 1.35), (-1.8, -1.35), (-1.52, -1.35)]
    for (x1, y1), (x2, y2) in zip(cy, cy[1:] + cy[:1]):
        b += line(x1, y1, x2, y2, "F.CrtYd", 0.05)
    b += circle(-1.95, -1.7, 0.05, "F.SilkS", 0.1)
    b += model(name)
    write(name, footprint(name, b, "InPlay IN100 QFN18 3x3 mm (IN100-Q1-R-RC1I): 0.4 mm pitch on the 7-pin sides, "
                          "0.5 mm on the 2-pin sides, EP 1.7 x 1.5 mm", "IN100 NanoBeacon QFN18", "smd"))
    parts = [("body", mesh_box(-1.5, -1.5, 0.0, 1.5, 1.5, 0.55)), ("mark", mesh_cyl(-1.0, -1.0, 0.55, 0.57, 0.18, 24))]
    wrl(name, parts)


XTAL_PADS = [("1", -0.525, 0.375), ("2", 0.525, 0.375), ("3", 0.525, -0.375), ("4", -0.525, -0.375)]


def xtal1612():
    name = "Crystal_SMD_1612-4Pin_1.6x1.2mm"
    b = txt("reference", "REF**", 0, -1.1, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, 1.1, "F.Fab", 0.3, 0.05, hide=True)
    for num, x, y in XTAL_PADS:
        b += smd(num, x, y, 0.6, 0.5, "rect")
    b += rect(-0.8, -0.6, 0.8, 0.6, "F.Fab", 0.08)
    b += rect(-0.875, -0.675, 0.875, 0.675, "F.CrtYd", 0.05)
    b += model(name)
    write(name, footprint(name, b, "1.6 x 1.2 mm four-pad crystal (TXC 8Q); pads 0.6 x 0.5 on a 1.05 x 0.75 mm grid",
                          "crystal 1612", "smd"))
    wrl(name, [("ceramic", mesh_box(-0.8, -0.6, 0.0, 0.8, 0.6, 0.12)),
               ("metal", mesh_box(-0.72, -0.52, 0.12, 0.72, 0.52, 0.35))])


def chip(name, px, pw, ph, cy_x, cy_y, L, W, H, body, descr, tags):
    b = txt("reference", "REF**", 0, -cy_y - 0.4, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, cy_y + 0.4, "F.Fab", 0.3, 0.05, hide=True)
    b += smd("1", -px, 0, pw, ph)
    b += smd("2", px, 0, pw, ph)
    b += rect(-L / 2, -W / 2, L / 2, W / 2, "F.Fab", 0.1)
    b += rect(-cy_x, -cy_y, cy_x, cy_y, "F.CrtYd", 0.05)
    b += model(name)
    write(name, footprint(name, b, descr, tags, "smd"))
    two_terminal_model(name, L, W, H, body, term=min(0.3, L * 0.2))


def passives():
    chip("C_0402_1005Metric", 0.48, 0.56, 0.62, 0.81, 0.36, 1.0, 0.5, 0.5, "cap",
         "Capacitor SMD 0402 (1005 metric), KiCad land pattern", "capacitor 0402")
    chip("R_0402_1005Metric", 0.51, 0.54, 0.64, 0.83, 0.37, 1.0, 0.5, 0.35, "body",
         "Resistor SMD 0402 (1005 metric), KiCad land pattern", "resistor 0402")
    chip("C_0805_2012Metric", 0.95, 1.0, 1.45, 1.5, 0.775, 2.0, 1.25, 1.25, "cap",
         "Capacitor SMD 0805 (2012 metric), KiCad land pattern", "capacitor 0805")


def sod523():
    name = "D_SOD-523"
    b = txt("reference", "REF**", 0, -1.0, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, 1.0, "F.Fab", 0.3, 0.05, hide=True)
    b += smd("1", -0.7, 0, 0.6, 0.7)      # cathode
    b += smd("2", 0.7, 0, 0.6, 0.7)       # anode
    b += rect(-0.6, -0.4, 0.6, 0.4, "F.Fab", 0.08)
    b += line(-0.35, -0.4, -0.35, 0.4, "F.Fab", 0.08)
    b += rect(-1.05, -0.42, 1.05, 0.42, "F.CrtYd", 0.05)
    b += line(-1.15, -0.4, -1.15, 0.4, "F.SilkS", 0.1)   # cathode bar
    b += model(name)
    write(name, footprint(name, b, "SOD-523 diode, KiCad land pattern; pad 1 = cathode", "diode SOD-523", "smd"))
    wrl(name, [("body", mesh_box(-0.6, -0.4, 0.0, 0.6, 0.4, 0.6)), ("mark", mesh_box(-0.45, -0.4, 0.6, -0.3, 0.4, 0.62))])


def pd0805():
    """Vishay TEMD7000X01: 0805 PIN photodiode, 2.0 x 1.25 x 0.85 mm. Pad 1 = cathode, pad 2 = anode."""
    name = "PD_0805_TEMD7000"
    b = txt("reference", "REF**", 0, -1.2, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, 1.2, "F.Fab", 0.3, 0.05, hide=True)
    b += smd("1", -0.9375, 0, 0.975, 1.4)
    b += smd("2", 0.9375, 0, 0.975, 1.4)
    b += rect(-1.0, -0.625, 1.0, 0.625, "F.Fab", 0.08)
    b += line(-0.6, -0.625, -0.6, 0.625, "F.Fab", 0.08)
    b += rect(-1.55, -0.78, 1.55, 0.78, "F.CrtYd", 0.05)   # pads + 0.125
    b += line(-1.62, -0.7, -1.62, 0.7, "F.SilkS", 0.1)   # cathode bar
    b += model(name)
    write(name, footprint(name, b, "Vishay TEMD7000X01 0805 photodiode; pad 1 = cathode (KiCad LED_0805 land pattern)",
                          "photodiode 0805 TEMD7000", "smd"))
    wrl(name, [("clear", mesh_box(-1.0, -0.625, 0.0, 1.0, 0.625, 0.85)),
               ("body", mesh_box(-0.3, -0.3, 0.84, 0.3, 0.3, 0.86))])


def sot23_3():
    name = "SOT-23-3"
    b = txt("reference", "REF**", 0, -2.2, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, 2.2, "F.Fab", 0.3, 0.05, hide=True)
    b += smd("1", -0.9375, -0.95, 1.475, 0.6)
    b += smd("2", -0.9375, 0.95, 1.475, 0.6)
    b += smd("3", 0.9375, 0, 1.475, 0.6)
    b += rect(-0.65, -1.45, 0.65, 1.45, "F.Fab", 0.08)
    b += rect(-1.92, -1.7, 1.92, 1.7, "F.CrtYd", 0.05)
    b += circle(-1.75, -1.65, 0.05, "F.SilkS", 0.1)
    b += model(name)
    write(name, footprint(name, b, "SOT-23 3-pin, KiCad land pattern (TPS3839DBZ: 1 GND, 2 RESET, 3 VDD)",
                          "SOT-23", "smd"))
    wrl(name, [("body", mesh_box(-0.65, -1.45, 0.05, 0.65, 1.45, 1.0))])


def x2son4():
    """TI X2SON-4 1 x 1 mm, 0.65 mm pitch (DQN0004A; TPS3831 / TPS3839 DQN): 1 RESET, 2 MR, 3 GND, 4 VDD, 5 thermal pad.
    Corner pads 0.46 x 0.31 mm chamfered towards the centre, as KiCad's Texas_X2SON-4 footprint; the thermal pad is
    a 0.46 mm square turned 45 deg (KiCad: 0.58 mm) so it keeps 0.14 mm from the signal pads."""
    name = "Texas_X2SON-4_1x1mm_P0.65mm"
    b = txt("reference", "REF**", 0, -1.1, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, 1.1, "F.Fab", 0.3, 0.05, hide=True)
    for num, x, y, corner in (("1", -0.43, -0.325, "bottom_right"), ("2", -0.43, 0.325, "top_right"),
                              ("3", 0.43, 0.325, "top_left"), ("4", 0.43, -0.325, "bottom_left")):
        b += smd(num, x, y, 0.46, 0.31, "roundrect", rr=0,
                 extra=f" (chamfer_ratio 0.5) (chamfer {corner}) (solder_paste_margin -0.04)")
    # v8.3: paste 0.04 mm inside every pad (0.38 x 0.23 mm on the pins), close to TI's DQN0004A stencil example,
    # because the pins sit only 0.14 mm from the thermal pad.
    b += smd("5", 0, 0, 0.46, 0.46, "roundrect", rr=0.15, rot=45, extra=" (solder_paste_margin -0.04)")
    b += rect(-0.5, -0.5, 0.5, 0.5, "F.Fab", 0.08)
    b += rect(-0.76, -0.58, 0.76, 0.58, "F.CrtYd", 0.05)
    b += circle(-0.7, -0.62, 0.05, "F.SilkS", 0.1)
    b += model(name)
    write(name, footprint(name, b, "TI X2SON-4 1x1 mm P0.65 mm (DQN0004A), TPS3831/TPS3839 DQN", "X2SON DQN TPS3831", "smd"))
    wrl(name, [("body", mesh_box(-0.5, -0.5, 0.0, 0.5, 0.5, 0.4)), ("mark", mesh_box(-0.42, -0.42, 0.4, -0.3, -0.3, 0.41))])


def sot363():
    name = "SOT-363_SC-70-6"
    pads = [("1", -0.95, -0.65), ("2", -0.95, 0), ("3", -0.95, 0.65), ("4", 0.95, 0.65), ("5", 0.95, 0), ("6", 0.95, -0.65)]
    b = txt("reference", "REF**", 0, -1.8, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, 1.8, "F.Fab", 0.3, 0.05, hide=True)
    for n, x, y in pads:
        b += smd(n, x, y, 0.65, 0.4)
    b += rect(-0.675, -1.0, 0.675, 1.0, "F.Fab", 0.08)
    b += rect(-1.6, -1.3, 1.6, 1.3, "F.CrtYd", 0.05)
    b += circle(-1.45, -1.2, 0.05, "F.SilkS", 0.1)
    b += model(name)
    write(name, footprint(name, b, "SOT-363 / SC-70-6, KiCad land pattern", "SOT-363 SC-70-6", "smd"))
    wrl(name, [("body", mesh_box(-0.625, -1.0, 0.05, 0.625, 1.0, 0.95))])


def lga12():
    name = "LGA-12_2x2mm_P0.5mm"
    pads = [("1", -0.7625, -0.75, 0.375, 0.35), ("2", -0.7625, -0.25, 0.375, 0.35), ("3", -0.7625, 0.25, 0.375, 0.35),
            ("4", -0.7625, 0.75, 0.375, 0.35), ("5", -0.25, 0.7625, 0.35, 0.375), ("6", 0.25, 0.7625, 0.35, 0.375),
            ("7", 0.7625, 0.75, 0.375, 0.35), ("8", 0.7625, 0.25, 0.375, 0.35), ("9", 0.7625, -0.25, 0.375, 0.35),
            ("10", 0.7625, -0.75, 0.375, 0.35), ("11", 0.25, -0.7625, 0.35, 0.375), ("12", -0.25, -0.7625, 0.35, 0.375)]
    b = txt("reference", "REF**", 0, -1.6, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, 1.6, "F.Fab", 0.3, 0.05, hide=True)
    for n, x, y, w, h in pads:
        b += smd(n, x, y, w, h, "rect")
    b += rect(-1.0, -1.0, 1.0, 1.0, "F.Fab", 0.08)
    b += rect(-1.25, -1.25, 1.25, 1.25, "F.CrtYd", 0.05)
    b += circle(-1.25, -1.25, 0.05, "F.SilkS", 0.1)
    b += model(name)
    write(name, footprint(name, b, "LGA-12 2x2 mm, 0.5 mm pitch (ST LSM303AGR / LIS2MDL), KiCad land pattern",
                          "LGA-12 LSM303AGR", "smd"))
    wrl(name, [("lga", mesh_box(-1.0, -1.0, 0.0, 1.0, 1.0, 1.0)), ("body", mesh_cyl(-0.6, -0.6, 1.0, 1.02, 0.1, 16))])


def lga10_bmp581():
    name = "Bosch_LGA-10_2x2mm_P0.5mm_BMP581"
    pads = [("1", 0.25, -0.7625, 0.27, 0.32), ("2", -0.25, -0.7625, 0.27, 0.32),
            ("3", -0.7625, -0.5, 0.32, 0.27), ("4", -0.7625, 0.0, 0.32, 0.27), ("5", -0.7625, 0.5, 0.32, 0.27),
            ("6", -0.25, 0.7625, 0.27, 0.32), ("7", 0.25, 0.7625, 0.27, 0.32),
            ("8", 0.7625, 0.5, 0.32, 0.27), ("9", 0.7625, 0.0, 0.32, 0.27), ("10", 0.7625, -0.5, 0.32, 0.27)]
    b = txt("reference", "REF**", 0, -1.6, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, 1.6, "F.Fab", 0.3, 0.05, hide=True)
    for n, x, y, w, h in pads:
        b += smd(n, x, y, w, h, "rect")
    b += rect(-1.0, -1.0, 1.0, 1.0, "F.Fab", 0.08)
    b += rect(-1.25, -1.25, 1.25, 1.25, "F.CrtYd", 0.05)
    b += circle(0.6, -1.25, 0.05, "F.SilkS", 0.1)
    b += model(name)
    write(name, footprint(name, b, "Bosch BMP581 LGA-10 2.0 x 2.0 x 0.75 mm; pad map from SparkFun's BMP581 Qwiic board. "
                          "Keep the vent hole on the lid clear", "LGA-10 BMP581 Bosch", "smd"))
    wrl(name, [("metal", mesh_box(-1.0, -1.0, 0.0, 1.0, 1.0, 0.75)), ("body", mesh_cyl(0.3, 0.3, 0.75, 0.77, 0.12, 16))])


def xiao_nrf52840():
    """Seeed XIAO nRF52840, SMD (castellated) mounting, from Seeed's OPL KiCad library (XIAO-nRF52840-SMD).
    Origin moved to the module centre; y down. USB-C end towards -y. Includes the bottom pads (SWD, VBAT/GND, NFC)."""
    name = "Seeed_XIAO_nRF52840_SMD"
    cx, cy = 8.9, -10.575          # centre of Seeed's 0..17.8 x -21.05..-0.1 outline (Seeed coords: y up = negative)

    def P(x, y):
        return round(x - cx, 4), round(y - cy, 4)
    b = txt("reference", "REF**", 0, -12.2, "F.Fab", 0.8, 0.12)
    b += txt("value", name, 0, 12.2, "F.Fab", 0.6, 0.1, hide=True)
    for i in range(7):
        x, y = P(0.835, -18.12 + 2.54 * i)
        b += smd(str(1 + i), x, y, 2.75, 2.0)
        x, y = P(17.0, -2.88 - 2.54 * i)
        b += smd(str(8 + i), x, y, 2.75, 2.0)
    for n, (x0, y0) in zip(("15", "16", "17", "18"), ((7.62, -19.0685), (10.16, -19.0685), (7.62, -16.5285), (10.16, -16.5285))):
        x, y = P(x0, y0)
        b += smd(n, x, y, 1.7, 1.7, "circle")
    for n, (x0, y0) in zip(("19", "20"), ((4.445, -10.8135), (4.445, -12.7185))):
        x, y = P(x0, y0)
        b += smd(n, x, y, 2.5, 1.1)
    for n, (x0, y0) in zip(("21", "22"), ((12.7, -1.2631), (14.605, -1.2631))):
        x, y = P(x0, y0)
        b += smd(n, x, y, 1.1, 2.5)
    x0, y0 = P(0, -21.05)
    x1, y1 = P(17.8, -0.1)
    b += rect(x0, y0, x1, y1, "F.Fab", 0.1)
    b += rect(x0 - 0.3, y0 - 1.8, x1 + 0.3, y1 + 0.3, "F.CrtYd", 0.05)
    ux0, uy0 = P(4.4, -22.55)
    ux1, uy1 = P(13.4, -21.05)
    b += rect(ux0, uy0, ux1, uy1, "F.Fab", 0.1)
    b += txt("user", "USB-C", 0, uy0 + 0.6, "F.Fab", 0.6, 0.1)
    b += model(name)
    write(name, footprint(name, b, "Seeed Studio XIAO nRF52840 surface-mounted by its castellated pads (Seeed OPL land "
                          "pattern), with the bottom VBAT/GND, SWD and NFC pads", "XIAO nRF52840 Seeed module", "smd"))
    wrl(name, [("pcb", mesh_box(x0, y0, 0.0, x1, y1, 1.0)),
               ("metal", mesh_box(-6.0, -7.5, 1.0, 6.0, 4.5, 2.5)),
               ("metal", mesh_box(ux0, uy0, 1.0, ux1, uy0 + 7.0, 4.2))])


def off_jumper():
    name = "SolderJumper_OFF_Tail"
    b = txt("reference", "REF**", 0, -0.9, "F.Fab", 0.4, 0.06)
    b += txt("value", "OFF", 0, 0.9, "F.Fab", 0.3, 0.05, hide=True)
    b += smd("1", 0.55, 0, 0.8, 1.0, "rect", '"F.Cu" "F.Mask"')
    b += smd("2", -0.55, 0, 0.8, 1.0, "rect", '"F.Cu" "F.Mask"')
    b += rect(-1.05, -0.6, 1.05, 0.6, "F.CrtYd", 0.05)
    write(name, footprint(name, b, "Open solder jumper, 0.3 mm gap: bridge to hold the tag off until the tail is cut",
                          "solder jumper", "smd exclude_from_pos_files exclude_from_bom allow_missing_courtyard"))


def wire_pad():
    name = "Antenna_WirePad_THT_D1.1mm_Drill0.6mm"
    b = txt("reference", "REF**", 0, -0.9, "F.Fab", 0.4, 0.06)
    b += txt("value", "ANT", 0, 0.9, "F.Fab", 0.3, 0.05, hide=True)
    b += tht("1", 0, 0, 1.1, 0.6)
    b += model(name)
    write(name, footprint(name, b, "Plated hole (0.6 mm drill, 1.1 mm pad) for a ~31 mm wire antenna", "antenna wire",
                          "through_hole exclude_from_pos_files exclude_from_bom allow_missing_courtyard"))
    wrl(name, [("copper", mesh_cyl(0, 0, -0.85, 0.2, 0.1, 16)),
               ("copper", mesh_cyl(0, 0, 0.2, 31.0, 0.1, 16, axis="x"))])


def edge_pad():
    """Top-side pad at the board edge for a wire (antenna or counterpoise): tinned by the paste stencil, the wire lies
    flat across it and leaves over the edge. Pad size from design.EDGE_PAD (along the edge-normal x along the edge).
    Local +x points out of the board."""
    sizes = getattr(D, "EDGE_PADS", None) or [getattr(D, "EDGE_PAD", (0.8, 1.1))]
    clr = getattr(D, "EDGE_PAD_CLEARANCE", None)
    extra = f" (clearance {clr})" if clr else ""
    for spec in sizes:
        w, h = spec[0], spec[1]
        side = spec[2] if len(spec) > 2 else "F"
        name = edge_pad_name(w, h, side)
        if side == "B":
            # Underside pad (no paste: JLC assembles the top only; the HASL finish tins it).
            b = txt("reference", "REF**", 0, -h / 2 - 0.4, "B.Fab", 0.4, 0.06, mirror=True)
            b += txt("value", "WIRE", 0, h / 2 + 0.4, "B.Fab", 0.3, 0.05, hide=True, mirror=True)
            b += smd("1", 0, 0, w, h, "roundrect", '"B.Cu" "B.Mask"', rr=0.15, extra=extra)
            b += line(-w / 2, 0, w / 2 + 1.0, 0, "B.Fab", 0.1)
            descr = "Underside wire pad at the board edge (antenna / counterpoise), no hole, no paste"
        else:
            b = txt("reference", "REF**", 0, -h / 2 - 0.4, "F.Fab", 0.4, 0.06)
            b += txt("value", "WIRE", 0, h / 2 + 0.4, "F.Fab", 0.3, 0.05, hide=True)
            b += smd("1", 0, 0, w, h, "roundrect", '"F.Cu" "F.Paste" "F.Mask"', rr=0.15, extra=extra)
            b += line(-w / 2, 0, w / 2 + 1.0, 0, "F.Fab", 0.1)
            descr = "Top-side wire pad at the board edge (antenna / counterpoise), no hole"
        write(name, footprint(name, b, descr, "antenna wire pad edge",
                              "smd exclude_from_pos_files exclude_from_bom allow_missing_courtyard"))


def edge_pad_name(w, h, side="F"):
    return (f"WirePad{'B' if side == 'B' else ''}_Edge_{w:.1f}x{h:.1f}mm").replace(".", "p")


def prog_pads():
    """2 x 2 plated pads on the tail, 1.6 mm pads at 2.54 mm: 3 RXD top-left, 2 TXD top-right, 1 GND bottom-left,
    4 VCC bottom-right (same order as v7, larger pads for pogo pins or hand soldering)."""
    name = "ProgPads_2x02_P2.54mm_D1.6mm_THT_Tab"
    b = txt("reference", "REF**", 0, -3.2, "F.Fab", 0.5, 0.08)
    b += txt("value", name, 0, 3.2, "F.Fab", 0.3, 0.05, hide=True)
    b += tht("3", -1.27, -1.27, 1.6, 0.8)
    b += tht("2", 1.27, -1.27, 1.6, 0.8)
    b += tht("1", -1.27, 1.27, 1.6, 0.8, "rect")
    b += tht("4", 1.27, 1.27, 1.6, 0.8)
    b += rect(-2.27, -2.27, 2.27, 2.27, "F.CrtYd", 0.05)
    write(name, footprint(name, b, "Programming pads on the cut-off tail, 2 x 2 at 2.54 mm, 1.6 mm pads: RXD TXD / GND VCC",
                          "programming pogo pads", "through_hole exclude_from_pos_files exclude_from_bom"))


def cell_pads_v8():
    """D1 cell interface. The cell sits under the tag, - cap facing the board.
    Pad 2 (-): bottom, solder-mask-defined 2.0 mm opening on a 2.6 mm copper disc (GND).
    Pad 1 (+): a bottom rim pad and a mirrored top rim pad, joined by two plated vias (pads '1' too).
    B.SilkS: outlines of the 4.8 mm (337) and 6.8 mm (364/377) cells. B.Fab: the crimp keep-out ring."""
    name = "Cell_Button_NegPad2mm_PlusEdge"
    px, py = D.PLUS_PAD
    w, h = D.PLUS_PAD_SIZE
    ang = D.PLUS_PAD_ANGLE
    b = txt("reference", "REF**", 0, 1.6, "B.Fab", 0.4, 0.06, mirror=True)
    b += txt("value", "cell", 0, 2.1, "B.Fab", 0.3, 0.05, hide=True, mirror=True)
    b += smd("1", px, py, w, h, "roundrect", '"B.Cu" "B.Mask"', rr=0.2, rot=ang)
    if getattr(D, "PLUS_TOP", True):
        b += smd("1", px, py, w, h, "roundrect", '"F.Cu" "F.Mask"', rr=0.2, rot=ang)
        for vx, vy in D.PLUS_VIAS:
            b += tht("1", vx, vy, 0.5, 0.3)
    b += smd("2", 0, 0, D.NEG_PAD_CU, D.NEG_PAD_CU, "circle", '"B.Cu" "B.Mask"',
             extra=f" (solder_mask_margin {round((D.NEG_PAD_D - D.NEG_PAD_CU) / 2, 3)})")
    for r in D.CELL_RINGS:
        b += circle(0, 0, r, "B.SilkS", 0.1)
    for r in D.KEEPOUT_RING:
        b += circle(0, 0, r, "B.Fab", 0.05)
    b += model(name)
    write(name, footprint(name, b, "Button cell under the tag: - cap on a 2.0 mm solder-mask-defined pad (silver epoxy), "
                          "+ wire from a rim pad on either side", "battery button cell 337 364 377",
                          "smd exclude_from_pos_files exclude_from_bom allow_missing_courtyard"))
    board_t = D.BOARD_THICKNESS
    z_top = -board_t - 0.05
    wrl(name, [("cell", mesh_cyl(0, 0, z_top - 1.65, z_top, 2.4, 48))])


def lipo_pads():
    name = "BatteryPads_LiPo_2x3mm"
    b = txt("reference", "REF**", 0, -2.4, "F.Fab", 0.5, 0.08)
    b += txt("value", name, 0, 2.4, "F.Fab", 0.3, 0.05, hide=True)
    b += smd("1", -1.6, 0, 2.2, 3.2, "roundrect", '"F.Cu" "F.Mask"', rr=0.15)
    b += smd("2", 1.6, 0, 2.2, 3.2, "roundrect", '"F.Cu" "F.Mask"', rr=0.15)
    b += rect(-2.9, -1.8, 2.9, 1.8, "F.CrtYd", 0.05)
    write(name, footprint(name, b, "Two 2.2 x 3.2 mm pads for a single-cell LiPo: 1 = BAT+, 2 = BAT-", "battery lipo pads",
                          "smd exclude_from_pos_files exclude_from_bom allow_missing_courtyard"))


def kikit_tab(width):
    name = f"KiKit_Tab_{width}mm".replace(".", "p")
    b = txt("reference", "REF**", -0.25, -2, "F.SilkS", 1, 0.15, hide=True)
    b += txt("value", "Tab", -3, -1, "Dwgs.User", 1.2, 0.2)
    b += (f'  (fp_text user "KIKIT: width: {width}mm" (at -5.5 0 90) (layer "Dwgs.User")\n'
          f'    (effects (font (size 1 1) (thickness 0.15)))\n    (tstamp {u()})\n  )\n')
    b += line(0, 0, -3, 0, "Dwgs.User", 0.3)
    b += line(0, 0, -1, -1, "Dwgs.User", 0.3)
    b += line(0, 0, -1, 1, "Dwgs.User", 0.3)
    b += line(0, 1, 0, -1, "Dwgs.User", 0.3)
    write(name, footprint(name, b, "KiKit tab annotation", "kikit tab",
                          "board_only exclude_from_pos_files exclude_from_bom allow_missing_courtyard"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(OUT3D, exist_ok=True)
    need = set(D.FOOTPRINTS)
    gens = {"in100": in100_qfn18, "xtal": xtal1612, "passives": passives, "sod523": sod523, "pd0805": pd0805,
            "sot23": sot23_3, "sot363": sot363, "x2son": x2son4, "lga12": lga12, "lga10": lga10_bmp581, "xiao": xiao_nrf52840,
            "off": off_jumper, "ant": wire_pad, "edgepad": edge_pad, "prog": prog_pads, "cell": cell_pads_v8, "lipo": lipo_pads}
    for k in need:
        gens[k]()
    for w in getattr(D, "TAB_WIDTHS", (1.0, 1.2)):
        kikit_tab(w)
    print(sorted(os.listdir(OUT)))
