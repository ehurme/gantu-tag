"""IN100 insect tag v8 D2: compact solar tag (no battery), 6.4 mm wide, about 1:2, programming tail at one end.

Tag coordinates: origin at the centre of the IN100, x right, y down (top view: photodiodes at the top, tail at the
bottom), mm. Top-side assembly only.

v8.2 (replaces the 4.5 x 24.6 mm v8.1 rod):
  - PD1..PD6 TEMD7000X01 in series, two columns of three, anode chain towards VCC, straight onto VCC: no blocking
    diode (it only cost string voltage; at night the tag is off anyway). C1 100 uF + C4 100 nF (at VDDQ). No 10 uF,
    no six/seven selector, no supercap.
  - S6: U2 TPS3831G18 (X2SON 1 x 1 mm, 1.67 V, 200 ms) drives CHIP_EN through D2 RB751S40; C5 330 nF holds CHIP_EN
    through a TX burst after U2 lets go; R2 3.3 Mohm lets it fall (tau 1.1 s), so the IN100 always starts at
    >= 1.69 V, makes one advert per start in poor light and switches off before a second one could take VCC under
    1.1 V (brown-out lock). S6L: R2 10 Mohm (tau 3.3 s, the v8.1 value), which survives an IN100 that waits one
    interval before its first advert but can lock if the IN100 stays on down to a low CHIP_EN (independent review F3/F6).
  - N6 (the minimal photodiodes-capacitor-resistor circuit): R1 1 Mohm VCC -> CHIP_EN with C5; U2, D2, R2 not fitted.
  - U1 at 0 deg: CHIP_EN/VCC face the start circuit above it, UART faces the tail, crystal pins left, RF right.
  - AE1 (RF, right edge) and AE2 (GND, lower left edge) are edge pads, labelled ANT and GND.
v8.3 (final test order, 0.6 mm board): AE1/AE2 moved to the underside (no parts there: easy to solder), 1.2 x 1.0 mm,
    RF_TX through one via inside AE1; the underside VCC trunk rerouted inboard to clear AE1.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts_lib import LIB, PARTDB, SYMBOLS_ALL, part, variant_value  # noqa: E402,F401

PROJECT = "insect_tag_v8_solar"
TITLE = "IN100 insect tag v8 D2: compact solar tag"
REV = "8.3"
SCH_COMMENT = "S6 / S6L / N6: six photodiodes straight onto 100 uF, 1.67 V start with hold, no battery"
BOARD_THICKNESS = 0.6
FOOTPRINTS = ["in100", "xtal", "passives", "edgepad", "prog", "pd0805", "sod523", "x2son"]
SYMBOLS = {k: SYMBOLS_ALL[k] for k in ("IN100_QFN18", "TPS3831DQN")}
POWER_SYMBOLS = {"VCC": "power:VCC", "GND": "power:GND"}
FLAG_NETS = ["VCC", "GND"]
FLAG_AT = (30, 120)
NOTES_AT = (20, 185)
SCH_PAPER = "A3"

# ---------------------------------------------------------------- outline
XH = 3.2                     # half-width: 6.4 mm
PD_PITCH = 1.6               # photodiode rows (0805 across the board, pads 1.4 mm tall)
PD_X = 1.57                  # photodiode column centres (+-): pads 0.2 mm from the long edges
Y_R3 = -5.95                 # photodiode row nearest the electronics
Y_ROWS = [round(Y_R3 - 2 * PD_PITCH, 3), round(Y_R3 - PD_PITCH, 3), Y_R3]
Y_TOP = round(Y_ROWS[0] - 1.0, 3)
Y_BOT = 2.4
R_CORNER = 0.8               # electronics end
R_CORNER_PD = 0.3            # photodiode end (the corner photodiodes sit 0.2 mm from both edges)
NECK_X0, NECK_X1, NECK_Y0, NECK_Y1 = -0.9, 0.9, Y_BOT - 0.4, Y_BOT + 1.3
CUT_Y = Y_BOT + 0.45
TAB_X0, TAB_X1, TAB_Y0, TAB_Y1 = -3.0, 3.0, NECK_Y1, NECK_Y1 + 6.6


def body_polygon():
    from shapely.geometry import box
    from shapely.ops import unary_union
    full = box(-XH, Y_TOP, XH, Y_BOT)
    top = full.buffer(-R_CORNER_PD, 32).buffer(R_CORNER_PD, 32).intersection(box(-9, Y_TOP - 1, 9, -4.0))
    bot = full.buffer(-R_CORNER, 32).buffer(R_CORNER, 32).intersection(box(-9, -4.0, 9, Y_BOT + 1))
    return unary_union([top, bot]).simplify(0.0005)


def outline_polygon():
    from shapely.geometry import box
    from shapely.ops import unary_union
    return unary_union([body_polygon(), box(NECK_X0, NECK_Y0, NECK_X1, NECK_Y1), box(TAB_X0, TAB_Y0, TAB_X1, TAB_Y1)])


# v8.3: both wire pads are on the UNDERSIDE, which carries no parts: nothing within 0.25 mm but solder-masked pour, so a
# wire is easy to solder (v8.2's top AE1 sat 0.17 mm from C1's GND pad, AE2 0.43 mm from IN100 pins). RF_TX reaches
# AE1 through one via inside the pad. The HASL finish tins them; no paste (JLC assembles the top only).
EDGE_PAD = (1.2, 1.0, "B")
EDGE_PADS = [EDGE_PAD]
EDGE_PAD_CLEARANCE = 0.25
AE1_XY = (XH - 0.22 - EDGE_PAD[0] / 2, -1.2)            # right edge, level with RF_TX (pin 16), underside
AE2_XY = (-(XH - 0.22 - EDGE_PAD[0] / 2), 1.0)          # left edge, lower corner, underside: diagonally opposite AE1
V_RF = (2.15, -1.2)                                     # RF_TX to the underside, inside AE1


def edge_fp(size):
    """Library id of the wire-pad footprint gen_footprints.edge_pad() writes for this size and side."""
    w, h = size[0], size[1]
    side = size[2] if len(size) > 2 else "F"
    name = f"WirePad{'B' if side == 'B' else ''}_Edge_{w:.1f}x{h:.1f}mm".replace(".", "p")
    return f"{LIB}:{name}"

# ---------------------------------------------------------------- parts (values = S6)
PARTS = [
    part("IN100", "U1", (0.0, 0.0, 0, "F"), (118, 80, 0), ref_at=(-11, -10, "left"), val_at=(3, 16, "left")),
    part("XTAL", "Y1", (-2.1, -2.6, 0, "F"), (80, 78, 0), ref_at=(2.5, -3, "left"), val_at=(2.5, 3.5, "left")),
    part("C100U", "C1", (1.53, -2.65, 0, "F"), (150, 104, 0), val_at=(2, 3, "left"), note="Energy store and burst reservoir"),
    part("C100N", "C4", (2.3, 1.0, 270, "F"), (194, 104, 0), val_at=(2, 3, "left"), note="At VDDQ (pin 13)"),
]
# Snake: PD1 top left -> PD2 top right -> PD3 middle right -> PD4 middle left -> PD5 bottom left -> PD6 bottom right.
PD_POS = [(-PD_X, 0, 0), (PD_X, 0, 0), (PD_X, 1, 180), (-PD_X, 1, 180), (-PD_X, 2, 0), (PD_X, 2, 0)]
PD_SCH_X = [30, 46, 62, 78, 94, 110]
for i, (x, row, rot) in enumerate(PD_POS):
    PARTS.append(part("PD", f"PD{i + 1}", (x, Y_ROWS[row], rot, "F"), (PD_SCH_X[i], 30, 0),
                      ref_at=(-3, -4, "left"), val_at=(-4, 4, "left")))
PARTS += [
    part("SUP_X2SON", "U2", (2.34, -4.35, 0, "F"), (60, 112, 0), ref_at=(-4, -5, "left"), val_at=(-4, 5, "left"),
         note="Start detector: releases 200 ms after VCC passes 1.67 V (S6)"),
    part("SCHOTTKY", "D2", (0.5, -4.675, 0, "F"), (90, 112, 0), ref_at=(-3, -4, "left"), val_at=(-4, 4, "left"),
         note="U2 can set CHIP_EN but not clear it (S6)"),
    part("C330N", "C5", (-0.93, -4.31, 270, "F"), (110, 126, 0), val_at=(2, 3, "left"),
         note="Holds CHIP_EN through a burst"),
    part("R3M3", "R2", (-1.68, -4.31, 270, "F"), (124, 126, 90), ref_at=(-2, -3, "left"), val_at=(-2, 3, "left"),
         note="Lets CHIP_EN fall: S6 3.3M (tau 1.1 s), S6L 10M (tau 3.3 s)"),
    part("R1M", "R1", (0.5, -3.85, 180, "F"), (110, 104, 90), dnp=True, ref_at=(-2, -3, "left"), val_at=(-2, 3, "left"),
         note="N6 only: CHIP_EN pull-up from VCC"),
    dict(ref="AE1", sym="Device:Antenna", value="Wire 31mm", fp=edge_fp(EDGE_PAD),
         fields={"Note": "~31 mm wire (quarter wave at 2.44 GHz) soldered flat on the edge pad; trim while watching RSSI"},
         sch=(180, 60, 0), pcb=(AE1_XY[0], AE1_XY[1], 0, "F"), in_bom=False),
    dict(ref="AE2", sym="Device:Antenna", value="Counterpoise (optional)", fp=edge_fp(EDGE_PAD),
         fields={"Note": "Optional ~31 mm GND wire leaving opposite AE1: dipole"},
         sch=(196, 60, 0), pcb=(AE2_XY[0], AE2_XY[1], 180, "F"), in_bom=False),
    dict(ref="J1", sym="Connector_Generic:Conn_01x04", value="PROG", fp=f"{LIB}:ProgPads_2x02_P2.54mm_D1.6mm_THT_Tab",
         fields={"Note": "2 x 2 pads on the cut-off tail: R(XD) T(XD) / G +. Programmer supplies 3.3 V"},
         sch=(60, 160, 0), pcb=(0.0, TAB_Y0 + 3.2, 0, "F"), in_bom=False, mirror="x",
         ref_at=(2, -5, "left"), val_at=(2, 3.5, "left")),
]
UNIT_ANCHOR = "U1"

NETS = {
    "VCC":  [("U1", "17"), ("U1", "13"), ("C1", "1"), ("C4", "1"), ("PD6", "2"), ("U2", "4"), ("R1", "1"),
             ("J1", "4")],
    "GND":  [("U1", "19"), ("Y1", "2"), ("Y1", "4"), ("C1", "2"), ("C4", "2"), ("C5", "2"), ("R2", "2"),
             ("U2", "3"), ("U2", "5"), ("PD1", "1"), ("J1", "1"), ("AE2", "1")],
    "S1":   [("PD1", "2"), ("PD2", "1")],
    "S2":   [("PD2", "2"), ("PD3", "1")],
    "S3":   [("PD3", "2"), ("PD4", "1")],
    "S4":   [("PD4", "2"), ("PD5", "1")],
    "S5":   [("PD5", "2"), ("PD6", "1")],
    "EN":   [("U1", "18"), ("D2", "1"), ("C5", "1"), ("R2", "1"), ("R1", "2")],
    "RST":  [("U2", "1"), ("D2", "2")],
    "XO_N": [("U1", "1"), ("Y1", "3")],
    "XO_P": [("U1", "2"), ("Y1", "1")],
    "TXD":  [("U1", "9"), ("J1", "2")],
    "RXD":  [("U1", "8"), ("J1", "3")],
    "RF":   [("U1", "16"), ("AE1", "1")],
}
NO_CONNECT = [("U1", n) for n in ("3", "4", "5", "6", "7", "10", "11", "12", "14", "15")] + [("U2", "2")]

VARIANTS = {
    "S6": dict(title="6 photodiodes, start circuit, 1.1 s hold", silk="S6 3M3", mark="S6", change={},
               why="U2 starts the IN100 at 1.67 V; C5/R2 (3.3M) hold CHIP_EN through one burst, then let it fall: "
                   "one advert per start in poor light, no brown-out lock."),
    "S6L": dict(title="6 photodiodes, start circuit, 3.3 s hold", silk="S6L 10M", mark="S6L",
                change={"R2": variant_value("R10M")},
                why="As S6 with R2 10M: still on for the second advert 3 s later. Works if the IN100 waits one "
                    "interval before its first advert; can lock in dim light if it stays on down to a low CHIP_EN."),
    "N6": dict(title="6 photodiodes, no start circuit", silk="N6", mark="N6",
               change={"U2": None, "D2": None, "R2": None, "R1": variant_value("R1M")},
               why="Photodiodes, capacitor, 1 M pull-up on CHIP_EN, IN100: the minimal circuit, as a comparison."),
}
VARIANT_PLACEHOLDER = "S6 3M3"
MARK_PLACEHOLDER = "S6"           # underside mark on the body; the panel scripts rewrite it per unit
PANEL_COLUMNS = ["S6"] * 4 + ["S6L"] * 4 + ["N6"] * 2

TAB_WIDTHS = (1.0, 1.2, 2.0, 3.0)
BOARD_ONLY = [
    dict(ref="KT1", fp=f"{LIB}:KiKit_Tab_1p0mm", pcb=(0.0, Y_TOP - 0.05, 270, "F")),        # far end -> rail
    # v8.3: no side tabs on the body. Both long edges carry parts within 0.2-0.3 mm of the edge (C1 0805 across the
    # break line, U2, the crystal, the photodiodes); a break there could crack C1 (a VCC-GND short) or U2's joints. The
    # body hangs from KT1 and the neck; the tail is held on three sides.
    dict(ref="KT4", fp=f"{LIB}:KiKit_Tab_3p0mm", pcb=(0.0, TAB_Y1 + 0.05, 90, "F")),  # tail end -> backbone
    # v8.3: the tail (cut off after programming) is anchored on three sides with wide tabs, so the 0.6 mm
    # panel stays stiff through printing and reflow; the nubs end up on scrap, not on the tag.
    dict(ref="KT5", fp=f"{LIB}:KiKit_Tab_2p0mm", pcb=(TAB_X0 - 0.04, round((TAB_Y0 + TAB_Y1) / 2, 3), 0, "F")),
    dict(ref="KT6", fp=f"{LIB}:KiKit_Tab_2p0mm", pcb=(TAB_X1 + 0.04, round((TAB_Y0 + TAB_Y1) / 2, 3), 180, "F")),
]

# ---------------------------------------------------------------- routing
VIA_D, VIA_DRILL = 0.5, 0.3
ZONE_CLEARANCE = 0.15
W_SIG, W_XO, W_PWR, W_RF = 0.13, 0.15, 0.2, 0.25
EP_VIAS = [(dx, dy) for dx in (-0.4, 0.4) for dy in (-0.45, 0.45)]
V13 = (2.35, -0.15)          # VDDQ to the underside VCC
V_C1 = (1.5, -2.65)          # VCC to the underside, between C1's pads (tented, under the body)
V_PD6 = (PD_X, Y_R3)         # string end (VCC) to the underside, between PD6's pads (tented, under the body)
V_G1 = (-2.35, -3.75)        # R2 / C5 / crystal lid return
V_G4 = (1.3, 1.95)           # C4 return
V_GPD = (-PD_X, Y_ROWS[0])   # PD1 cathode to the underside GND, between PD1's pads (tented, under the body)
GND_VIAS = [V_G1, V_G4, V_GPD]
VCC_VIAS = [V13, V_C1, V_PD6]
EN_VIAS = []
J1Y = TAB_Y0 + 3.2
X_RXD_N, X_TXD_N, X_GND_N, X_VCC_N = -0.3, 0.3, -0.3, 0.4   # v8.3: underside GND/VCC 0.4 mm apart across CUT (was 0.15)


def static_tracks():
    # Photodiode string: a snake through the 2 x 3 block, every link a short hop between neighbouring pads.
    for k in range(1, 6):
        yield (f"S{k}", "F", W_PWR, [(f"PD{k}", "2"), (f"PD{k + 1}", "1")])
    yield ("GND", "F", W_PWR, [("PD1", "1"), V_GPD])
    # VCC on top: string end -> U2 VDD; R1 (N6) <- C1 <- pin 17. The two meet on the underside (V_PD6 - V_C1).
    yield ("VCC", "F", W_PWR, [("PD6", "2"), V_PD6])
    yield ("VCC", "F", W_PWR, [("PD6", "2"), ("U2", "4")])
    yield ("VCC", "F", W_PWR, [("U1", "17"), ("C1", "1")])
    yield ("VCC", "F", W_PWR, [("C1", "1"), V_C1])
    yield ("VCC", "F", W_PWR, [("C1", "1"), ("R1", "1")])
    # Start circuit: U2 RESET -> D2 -> CHIP_EN node (D2 cathode, C5, R2, R1), then via the underside to pin 18.
    yield ("RST", "F", W_SIG, [("U2", "1"), ("D2", "2")])
    yield ("EN", "F", W_SIG, [("D2", "1"), ("C5", "1")])
    yield ("EN", "F", W_SIG, [("C5", "1"), ("R2", "1")])
    yield ("EN", "F", W_SIG, [("D2", "1"), ("R1", "2")])
    yield ("EN", "F", W_SIG, [("R1", "2"), (-0.25, -3.4), ("U1", "18")])
    # Returns.
    yield ("GND", "F", W_PWR, [("U2", "3"), ("U2", "5")])
    yield ("GND", "F", W_PWR, [("U2", "3"), ("C1", "2")])
    yield ("GND", "F", W_PWR, [("C5", "2"), ("R2", "2")])
    yield ("GND", "F", W_PWR, [("R2", "2"), V_G1])
    yield ("GND", "F", W_PWR, [("Y1", "4"), V_G1])
    yield ("GND", "F", W_PWR, [("Y1", "2"), (-1.3, -1.95), (-0.8, -1.4), (-0.6, -0.85)])
    yield ("GND", "F", W_PWR, [("C4", "2"), V_G4])
    # Crystal: XO_P up the outer left lane into pad 1; XO_N up between the crystal's pad columns into pad 3.
    yield ("XO_P", "F", W_XO, [("U1", "2"), (-2.6, -0.8), (-2.6, -1.975), ("Y1", "1")])
    yield ("XO_N", "F", W_XO, [("U1", "1"), (-2.1, -1.5), (-2.1, -2.975), ("Y1", "3")])
    # RF, VDDQ.
    yield ("RF", "F", W_RF, [("U1", "16"), V_RF])
    yield ("VCC", "F", W_PWR, [("U1", "13"), V13])
    yield ("VCC", "F", W_PWR, [("U1", "13"), (2.0, 0.0), ("C4", "1")])
    # UART straight down through the neck to the pads (as D1).
    yield ("RXD", "F", W_SIG, [("U1", "8"), (X_RXD_N, 2.0), (X_RXD_N, TAB_Y0 + 0.5), ("J1", "3")])
    yield ("TXD", "F", W_SIG, [("U1", "9"), (X_TXD_N, 2.0), (X_TXD_N, TAB_Y0 + 0.5), ("J1", "2")])
    # Underside VCC: string end -> C1 -> VDDQ -> neck -> J1 +; GND lane from the exposed pad to J1 G.
    yield ("VCC", "B", 0.3, [V_PD6, V_C1, (1.35, -2.35), (1.35, -0.3), V13, (2.0, 1.1), (X_VCC_N, 1.45),
                             (X_VCC_N, TAB_Y0 + 0.3),
                             (2.35, TAB_Y0 + 0.65), (2.35, J1Y + 0.5), ("J1", "4")])
    yield ("GND", "B", 0.3, [(X_GND_N, 0.9), (X_GND_N, TAB_Y0 + 0.2), (0.0, TAB_Y0 + 0.5), (0.0, J1Y + 0.5),
                             ("J1", "1")])


def static_vias():
    for x, y in EP_VIAS:
        yield ("GND", x, y)
    for v in GND_VIAS:
        yield ("GND",) + v
    for v in VCC_VIAS:
        yield ("VCC",) + v
    for v in EN_VIAS:
        yield ("EN",) + v
    yield ("RF",) + V_RF


ZONES = [dict(layer="F", net="GND", pts=None), dict(layer="B", net="GND", pts=None)]


def _zones():
    """Bottom: the whole tag (not the tail). Top: the electronics only (no pour between the photodiodes)."""
    from shapely.geometry import box
    ZONES[0]["pts"] = [tuple(p) for p in body_polygon().intersection(box(-9, Y_R3 + 0.75, 9, 9)).exterior.coords][:-1]
    ZONES[1]["pts"] = [tuple(p) for p in body_polygon().exterior.coords][:-1]


_zones()

SILK_TEXT = [("CUT", 0.0, CUT_Y + 0.42, 0.42, "F", 0),
             ("R", -1.27, TAB_Y0 + 0.75, 0.5, "F", 0), ("T", 1.27, TAB_Y0 + 0.75, 0.5, "F", 0),
             ("G", -2.45, J1Y + 1.27, 0.6, "F", 0), ("+", 2.45, J1Y + 1.27, 0.6, "F", 0),
             ("S6 3M3", 0.0, TAB_Y0 + 5.85, 0.7, "F", 0),
             ("ANT", 0.72, AE1_XY[1], 0.6, "B", 0, 0.12),     # underside, beside AE1: the RF wire
             (MARK_PLACEHOLDER, 0.0, -7.4, 1.0, "B", 0, 0.15),  # underside variant mark (stays after the tail is cut)
             ("GND", -0.68, AE2_XY[1] + 0.12, 0.6, "B", 0, 0.12)]  # underside, beside AE2: optional GND wire
SILK_LINES = [((NECK_X0, CUT_Y), (NECK_X1, CUT_Y), "F")]
SCH_NOTES = [
    "IN100 insect tag v8 D2 (compact solar): photodiode string straight onto 100 uF, 1.67 V start with hold, no battery",
    "- PD1-PD6 TEMD7000X01 in series, anodes towards VCC, no blocking diode.",
    "- C1 100 uF + C4 100 nF store charge for the TX bursts.",
    "- S6: U2 TPS3831G18 sets CHIP_EN through D2 200 ms after VCC passes 1.67 V; C5 holds it, R2 discharges it.",
    "- R2: S6 3.3M (tau 1.1 s, one advert per start in poor light), S6L 10M (tau 3.3 s).",
    "- N6: R1 1M from VCC to CHIP_EN with C5; U2, D2, R2 not fitted.",
    "- Program at 3.3 V through J1 (GND, RXD, TXD, +) on the tail, then cut the tail off.",
]
