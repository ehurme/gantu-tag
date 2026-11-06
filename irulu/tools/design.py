"""IN100 insect tag v8 D1: battery tag, 7.2 mm round, cut-to-start tail, V1 slow enable / V2 OFF-jumper panel.

Tag coordinates: origin at the centre of the round tag and of the cell under it (the IN100 sits 1.2 mm below it);
x right, y down (top view), mm.

v8.1 (compact, same parts as v8.0; see README):
  - Disc 7.2 mm (v8.0: 8.0 mm plus antenna lobes). C1 0805 centred across the top, R1 under it, C2
    upright in the top-left corner, the crystal on the left, C4 at VDDQ on the right.
  - Antenna and counterpoise wires on top-side edge pads: AE1 (RF, 0.8 x 1.1 mm) on the right rim next to RF_TX,
    AE2 (GND, 0.8 x 0.8 mm) at the lower left.
  - The cell's - cap sits on a 2.0 mm solder-mask-defined GND pad; + on a 0.9 x 1.2 mm underside pad at the
    upper-right rim (the VCC via is in it).
  - Bottom-side crimp keep-out r = 1.65 ... 3.70 mm: no exposed copper and no non-VCC vias except three tented ones at
    r = 1.70 mm (two exposed-pad GND vias and the CHIP_EN via).
  - CHIP_EN: top layer from the IN100 to R1, then a via to the underside between R1 and C2, round the left to the
    neck and back up on the tail for the OFF jumper.
  - Variants: V1 slow enable (1 M / 100 nF, tau 0.1 s: CHIP_EN rises well after a 337 has charged C1) and
    V2 (1 M / 1 nF + OFF jumper: bridge OFF, fit the cell, cut the tail to start). v8.1 V1 was SparkFun's 1 k / 100 nF,
    which races a 337's 4-20 ms charge-up of C1 (independent review, F2).
v8.3 (final test order, 0.6 mm board): AE1 moved to the upper-right rim (-19 deg) and enlarged (>= 0.75 mm free);
    AE2 slimmer and moved to 147 deg (0.36 mm free instead of 0.20); V2's enable is now 100 k / 10 nF (hedges an unpublished CHIP_EN input
    load); side tabs at matching heights. Copper otherwise as v8.2.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parts_lib import LIB, PARTDB, SYMBOLS_ALL, part, variant_value  # noqa: E402,F401

PROJECT = "insect_tag_v8_battery"
TITLE = "IN100 insect tag v8 D1: battery tag"
REV = "8.3"
SCH_COMMENT = "V1 slow enable 1M/100nF / V2 100k/10nF + OFF jumper (cut-to-start). Cell centred on the IN100"
BOARD_THICKNESS = 0.6
FOOTPRINTS = ["in100", "xtal", "passives", "off", "edgepad", "prog", "cell"]
SYMBOLS = {k: SYMBOLS_ALL[k] for k in ("IN100_QFN18",)}
POWER_SYMBOLS = {"VCC": "power:VCC", "GND": "power:GND"}
FLAG_NETS = ["VCC", "GND"]
FLAG_AT = (40, 100)
NOTES_AT = (20, 132)

# ---------------------------------------------------------------- outline
R_TAG = 3.6                         # 7.2 mm round, no lobes: the antenna wires go on top-side edge pads
TY = round(R_TAG - 3.9, 3)          # the tail was laid out for a 7.8 mm disc; it moves up with the disc's lower edge


def ty(y):
    return round(y + TY, 3)


NECK_X0, NECK_X1, NECK_Y0, NECK_Y1 = -0.9, 0.9, 3.2, ty(5.3)
TAB_X0, TAB_X1, TAB_Y0, TAB_Y1 = -3.0, 3.0, ty(5.3), ty(13.2)
CUT_Y = ty(4.35)


def _pol(r, deg):
    a = math.radians(deg)
    return (round(r * math.cos(a), 3), round(r * math.sin(a), 3))


# v8.3: AE1 moved to the roomiest stretch of the rim (searched numerically) and enlarged: >= 0.75 mm to every other-net
# pad (v8.2: 0.29 mm from C4). AE2 stays between the crystal and U1, the only GND-safe spot on the left (the top-left
# is C1's and C2's pads), as a slimmer pad hugging the rim: 0.36 mm clear instead of 0.20. Local clearance 0.25 mm keeps
# the GND pour further from AE1.
EDGE_PAD = (1.2, 0.9)               # antenna wire pad: along the radius x along the rim
EDGE_PAD2 = (0.5, 0.9)              # counterpoise pad (optional GND wire): slim, it hugs the rim between Y1 and U1
EDGE_PADS = [EDGE_PAD, EDGE_PAD2]
EDGE_PAD_CLEARANCE = 0.25
AE1_ANG, AE2_ANG = -19.0, 147.0     # AE1 (RF) upper right, just above RF_TX; AE2 (GND) lower left, about opposite
AE1_XY = _pol(2.7, AE1_ANG)
AE2_XY = _pol(3.05, AE2_ANG)


def edge_fp(size, side="F"):
    """Library id of the wire-pad footprint gen_footprints.edge_pad() writes for this size and side."""
    w, h = size
    name = f"WirePad{'B' if side == 'B' else ''}_Edge_{w:.1f}x{h:.1f}mm".replace(".", "p")
    return f"{LIB}:{name}"


def tag_polygon():
    from shapely.geometry import Point
    return Point(0, 0).buffer(R_TAG, 256)


def outline_polygon():
    from shapely.geometry import box
    from shapely.ops import unary_union
    return unary_union([tag_polygon(), box(NECK_X0, NECK_Y0, NECK_X1, NECK_Y1), box(TAB_X0, TAB_Y0, TAB_X1, TAB_Y1)])


def pour_pts():
    return [tuple(p) for p in tag_polygon().exterior.coords][:-1]


# ---------------------------------------------------------------- cell interface
NEG_PAD_D = 2.0           # solder-mask opening (what the epoxy sees)
NEG_PAD_CU = 2.6          # copper under it (mask-defined pad)
PLUS_ANG = -55.0          # underside + pad, upper right, outside the 337 outline
PLUS_C = _pol(2.9, PLUS_ANG)
PLUS_PAD = PLUS_C
PLUS_PAD_SIZE = (0.9, 1.2)  # radial x tangential: r 2.45 .. 3.35
PLUS_PAD_ANGLE = -PLUS_ANG
PLUS_TOP = False          # no top + pad: the top rim is full; a 6.8 mm can sits on the underside pad itself
PLUS_VIAS = []
CELL_RINGS = (2.4, 3.4)   # B.SilkS: 4.8 mm (337) and 6.8 mm (364/377) cell outlines
KEEPOUT_RING = (1.65, 3.70)

# ---------------------------------------------------------------- parts (values = V1 Reference)
PARTS = [
    part("IN100", "U1", (0.0, 1.2, 0, "F"), (118, 76, 0), ref_at=(-11, -10, "left"), val_at=(3, 16, "left")),
    part("XTAL", "Y1", (-2.55, -0.05, 90, "F"), (80, 74, 0), ref_at=(2.5, -3, "left"), val_at=(2.5, 3.5, "left")),
    part("C100U", "C1", (0.0, -2.3, 180, "F"), (146, 100, 0), val_at=(2, 3, "left"), note="Bulk reservoir for TX bursts"),
    part("C100N", "C4", (2.2, 1.5, 270, "F"), (190, 100, 0), val_at=(2, 3, "left"), note="Right at VDDQ (pin 13)"),
    part("R1M", "R1", (0.0, -1.1, 0, "F"), (100, 56, 0),
         note="CHIP_EN pull-up. V1: 1M (C26083). V2: 100k (C25741)"),
    part("C100N", "C2", (-1.9, -1.8, 90, "F"), (88, 56, 0),
         note="CHIP_EN delay. V1: 100nF (C1525), tau 0.1 s. V2: 10nF (C15195), tau 1 ms"),
    dict(ref="JP1", sym="Jumper:SolderJumper_2_Open", value="OFF", fp=f"{LIB}:SolderJumper_OFF_Tail",
         fields={"Note": "Bridge after programming, before fitting the cell (V2; optional on V1); cutting the tail "
                         "starts the tag. Bridged: 1.55 uA through R1 on V1, 15.5 uA on V2 (100k)"},
         sch=(92, 118, 0), pcb=(-1.1, ty(11.65), 180, "F"), in_bom=False),
    dict(ref="AE1", sym="Device:Antenna", value="Wire 31mm", fp=edge_fp(EDGE_PAD),
         fields={"Note": "~31 mm wire (quarter wave at 2.44 GHz) soldered flat on the edge pad; trim while watching RSSI"},
         sch=(150, 52, 0), pcb=(AE1_XY[0], AE1_XY[1], -AE1_ANG, "F"), in_bom=False),
    dict(ref="AE2", sym="Device:Antenna", value="Counterpoise (optional)", fp=edge_fp(EDGE_PAD2),
         fields={"Note": "Optional ~31 mm GND wire leaving opposite AE1: dipole"},
         sch=(166, 52, 0), pcb=(AE2_XY[0], AE2_XY[1], -AE2_ANG, "F"), in_bom=False),
    dict(ref="BT1", sym="Device:Battery_Cell", value="337 / 364 / 377", fp=f"{LIB}:Cell_Button_NegPad2mm_PlusEdge",
         fields={"Note": "Fitted by the builder: - cap silver-epoxied to the underside pad, + to the underside rim pad"},
         sch=(176, 100, 0), pcb=(0.0, 0.0, 0, "F"), in_bom=False),
    dict(ref="J1", sym="Connector_Generic:Conn_01x04", value="PROG", fp=f"{LIB}:ProgPads_2x02_P2.54mm_D1.6mm_THT_Tab",
         fields={"Note": "2 x 2 pads on the cut-off tail: R(XD) T(XD) / G +"},
         sch=(70, 110, 0), pcb=(0.0, ty(8.5), 0, "F"), in_bom=False, mirror="x",
         ref_at=(2, -5, "left"), val_at=(2, 3.5, "left")),
]

# U1 (QFN18): 1 XO_N, 2 XO_P, 3-7 NC, 8 GPIO0 (RXD), 9 GPIO1 (TXD), 10-12 NC, 13 VDDQ, 14/15 RTC (NC), 16 RF_TX,
# 17 VCC, 18 CHIP_EN, 19 EP/GND
NETS = {
    "VCC":  [("U1", "17"), ("U1", "13"), ("C1", "1"), ("C4", "1"), ("R1", "2"), ("BT1", "1"), ("J1", "4")],
    "GND":  [("U1", "19"), ("Y1", "2"), ("Y1", "4"), ("C1", "2"), ("C4", "2"), ("C2", "2"), ("JP1", "2"),
             ("BT1", "2"), ("J1", "1"), ("AE2", "1")],
    "EN":   [("U1", "18"), ("R1", "1"), ("C2", "1"), ("JP1", "1")],
    "XO_N": [("U1", "1"), ("Y1", "3")],
    "XO_P": [("U1", "2"), ("Y1", "1")],
    "TXD":  [("U1", "9"), ("J1", "2")],
    "RXD":  [("U1", "8"), ("J1", "3")],
    "RF":   [("U1", "16"), ("AE1", "1")],
}
NO_CONNECT = [("U1", n) for n in ("3", "4", "5", "6", "7", "10", "11", "12", "14", "15")]

# ---------------------------------------------------------------- variants (population only; identical copper)
VARIANTS = {
    "V1": dict(title="Slow enable", silk="V1 SLOW", mark="V1", change={},
               why="1 M / 100 nF enable (tau 0.1 s): CHIP_EN rises after the cell has charged C1, so the cell can be "
                   "fitted live. Program 0 dBm, 3 s (+4 dBm only on 364/377 cells)."),
    "V2": dict(title="OFF jumper, 100k enable", silk="V2 OFF", mark="V2",
               change={"R1": variant_value("R100K"), "C2": variant_value("C10N")},
               why="100 k / 10 nF enable (tau 1 ms) + OFF jumper: bridge OFF before fitting the cell (15.5 uA while "
                   "bridged), cut the tail to start. The 100 k still lifts CHIP_EN past 0.6 VCC if the IN100 turns out "
                   "to load the pin (unpublished) with anything down to ~150 kohm or up to ~6 uA, where V1's 1 M "
                   "would fail. Program 0 dBm, 3 s (+4 dBm only on 364/377 cells)."),
}
VARIANT_PLACEHOLDER = "V1 SLOW"
MARK_PLACEHOLDER = "V1"           # underside mark on the body, between the cell outlines; rewritten per unit
PANEL_COLUMNS = ["V1"] * 5 + ["V2"] * 5

# KiKit tab annotations (just outside an edge, arrow pointing in); mouse bites sit in the tab (offset -0.25 mm).
def _side_tab(deg, width=1.0):
    """Origin for a horizontal (left/right) tab on the round rim: both of the tab's side rays must start outside the
    disc, so the origin sits just outside the rim at the side nearer the disc's equator."""
    y = R_TAG * math.sin(math.radians(deg))
    yn = max(abs(y) - width / 2, 0.0)
    x = math.sqrt(R_TAG ** 2 - yn ** 2) + 0.03
    return (round(math.copysign(x, math.cos(math.radians(deg))), 3), round(y, 3))


def _top_tab(x, width=1.0):
    """Origin for a vertical tab on the top of the rim at x: both side rays must start outside the disc."""
    xn = max(abs(x) - width / 2, 0.0)
    return (round(x, 3), round(-math.sqrt(R_TAG ** 2 - xn ** 2) - 0.03, 3))


# v8.3: KT1 moved right of AE2 (x = 0.93, 285 deg); KT2 at 155 deg so both side tabs sit at the same height and
# meet their neighbours' tabs squarely (v8.2: 170/25 deg, offset by 0.9 mm, joined by a 0.4 mm Z-shaped neck).
TAB_WIDTHS = (1.0, 1.2, 2.0, 3.0)
BOARD_ONLY = [
    dict(ref="KT1", fp=f"{LIB}:KiKit_Tab_1p0mm", pcb=(_top_tab(0.93)[0], _top_tab(0.93)[1], 270, "F")),
    dict(ref="KT2", fp=f"{LIB}:KiKit_Tab_1p0mm", pcb=(_side_tab(155)[0], _side_tab(155)[1], 0, "F")),
    dict(ref="KT3", fp=f"{LIB}:KiKit_Tab_1p0mm", pcb=(_side_tab(25)[0], _side_tab(25)[1], 180, "F")),
    dict(ref="KT4", fp=f"{LIB}:KiKit_Tab_3p0mm", pcb=(0.0, TAB_Y1 + 0.05, 90, "F")),  # tail end -> backbone
    # v8.3: the tail (cut off after programming) is anchored on three sides with wide tabs, so the 0.6 mm
    # panel stays stiff through printing and reflow; the nubs end up on scrap, not on the tag.
    dict(ref="KT5", fp=f"{LIB}:KiKit_Tab_2p0mm", pcb=(TAB_X0 - 0.04, round((TAB_Y0 + TAB_Y1) / 2 + 0.6, 3), 0, "F")),
    dict(ref="KT6", fp=f"{LIB}:KiKit_Tab_2p0mm", pcb=(TAB_X1 + 0.04, round((TAB_Y0 + TAB_Y1) / 2 + 0.6, 3), 180, "F")),
]

# ---------------------------------------------------------------- routing
VIA_D, VIA_DRILL = 0.5, 0.3
ZONE_CLEARANCE = 0.15
W_SIG, W_XO, W_PWR, W_RF = 0.13, 0.15, 0.2, 0.25
EP_VIAS = [(dx, 1.2 + dy) for dx in (-0.4, 0.4) for dy in (-0.45, 0.45)]
V_EN = (-1.25, -1.15)         # CHIP_EN to the underside between R1 and C2 (tented; inner edge of the crimp ring)
V_EN_TAIL = (-2.35, ty(6.3))  # CHIP_EN back to the top on the tail, for the OFF jumper
V_VCC_A = (1.95, -2.3)        # VCC to the underside, inside the underside + pad
V_VCC_B = (2.85, 1.0)         # VCC at VDDQ / C4
X_EN_B, X_GND_B, X_VCC_B = -0.55, -0.05, 0.52  # neck lanes, underside (v8.3: >= 0.29 mm apart across CUT, was 0.15)
X_RXD_N, X_TXD_N = -0.3, 0.3                    # neck lanes, top
GND_VIAS = []


def static_tracks():
    # Crystal: XO_P across into pad 1; XO_N between the crystal's pad rows to pad 3.
    yield ("XO_P", "F", W_XO, [("U1", "2"), (-2.0, 0.4), ("Y1", "1")])
    yield ("XO_N", "F", W_XO, [("U1", "1"), (-1.75, 0.0), (-1.85, -0.05), (-2.92, -0.05), ("Y1", "3")])
    # RF straight right to the edge pad.
    yield ("RF", "F", W_RF, [("U1", "16"), (2.0, 0.0), ("AE1", "1")])
    # Top row: EN left of the U1 top pins, VCC right. R1 bridges them; EN goes on past the via to C2 (upright, top
    # left); C1 across the top on VCC.
    yield ("EN", "F", W_SIG, [("U1", "18"), (-0.25, -0.75), ("R1", "1")])
    yield ("EN", "F", W_SIG, [("R1", "1"), V_EN])
    yield ("EN", "F", W_SIG, [V_EN, ("C2", "1")])
    yield ("VCC", "F", W_PWR, [("U1", "17"), (0.25, -0.75), ("R1", "2")])
    yield ("VCC", "F", W_PWR, [("R1", "2"), ("C1", "1")])
    yield ("VCC", "F", W_PWR, [("C1", "1"), V_VCC_A])
    # VDDQ to C4 and the right-hand VCC via.
    yield ("VCC", "F", W_PWR, [("U1", "13"), (2.0, 1.2), ("C4", "1")])
    yield ("VCC", "F", W_PWR, [("C4", "1"), V_VCC_B])
    # UART on top straight down the neck to the pads.
    yield ("RXD", "F", W_SIG, [("U1", "8"), (X_RXD_N, 3.3), (X_RXD_N, ty(5.8)), ("J1", "3")])
    yield ("TXD", "F", W_SIG, [("U1", "9"), (X_TXD_N, 3.3), (X_TXD_N, ty(5.8)), ("J1", "2")])
    # Underside: CHIP_EN round the left, VCC round the right (both under solder mask), GND from the - pad down.
    yield ("EN", "B", W_SIG, [V_EN, (-2.05, -0.75), (-2.2, 1.0), (-1.35, 2.55), (X_EN_B, 3.2), (X_EN_B, ty(5.6)),
                              V_EN_TAIL])
    yield ("VCC", "B", 0.3, [V_VCC_A, (2.75, -1.0), V_VCC_B, (2.2, 2.35), (X_VCC_B, 3.2), (X_VCC_B, ty(5.6)),
                             (2.35, ty(5.95)), (2.35, ty(9.0)), ("J1", "4")])
    yield ("VCC", "B", 0.3, [V_VCC_A, ("BT1", "1")])
    yield ("GND", "B", 0.25, [(X_GND_B, 1.2), (X_GND_B, ty(9.0)), ("J1", "1")])
    # Tail: OFF jumper between CHIP_EN and GND.
    yield ("EN", "F", W_SIG, [V_EN_TAIL, (-2.35, ty(11.65)), ("JP1", "1")])
    yield ("GND", "F", W_PWR, [("JP1", "2"), (-0.55, ty(10.8)), ("J1", "1")])


def static_vias():
    for x, y in EP_VIAS:
        yield ("GND", x, y)
    for v in GND_VIAS:
        yield ("GND",) + v
    for v in (V_EN, V_EN_TAIL):
        yield ("EN",) + v
    for v in (V_VCC_A, V_VCC_B):
        yield ("VCC",) + v


ZONES = [dict(layer="F", net="GND", pts=None), dict(layer="B", net="GND", pts=None)]


def _fill_zone_pts():
    ZONES[0]["pts"] = pour_pts()
    ZONES[1]["pts"] = pour_pts()


_fill_zone_pts()

# Silkscreen (text, x, y, size, side, angle) and lines
SILK_TEXT = [("CUT", 0.0, ty(4.8), 0.42, "F", 0),
             ("R", -1.27, ty(6.05), 0.5, "F", 0), ("T", 1.27, ty(6.05), 0.5, "F", 0),
             ("G", -2.45, ty(9.77), 0.6, "F", 0), ("+", 2.45, ty(9.77), 0.6, "F", 0),
             ("OFF", 0.75, ty(11.65), 0.55, "F", 0),
             ("+", _pol(2.75, -80)[0], _pol(2.75, -80)[1], 0.6, "B", 0),
             ("-", -1.85, -0.5, 0.8, "B", 0, 0.12),           # beside the round pad: the cell's - cap goes there
             (MARK_PLACEHOLDER, 0.0, 2.88, 0.6, "B", 0, 0.12),  # variant mark, outside a 337, under a 6.8 mm cell
             ("ANT", 2.6, 0.24, 0.5, "F", 0, 0.1),          # below AE1 (the RF wire pad, upper right)
             ("V1 SLOW", 0.0, ty(12.65), 0.55, "F", 0)]
SILK_LINES = [((NECK_X0, CUT_Y), (NECK_X1, CUT_Y), "F")]

SCH_NOTES = [
    "IN100 insect tag v8 D1 (battery): cell centred on the IN100, cut-to-start tail",
    "- U1 IN100 QFN18 (JLC C6062024). VDDQ tied to VCC. 4 EP vias, under the cell's - cap.",
    "- C1 100 uF 0805 (bursts), C4 100 nF at VDDQ (pin 13).",
    "- CHIP_EN: R1 to VCC, C2 to GND. V1 1M/100nF (tau 0.1 s, slow start), V2 100k/10nF + JP1 OFF on the tail.",
    "- Y1 26 MHz 1612, 7 pF, 80 ohm (IN100 spec 6-8 pF, 60-100 ohm): on-chip load capacitance.",
    "- AE1 ~31 mm wire on a top edge pad (upper right) from RF_TX (on-chip 50 ohm match). AE2 optional GND arm (top).",
    "- BT1: 337/364/377 silver-oxide cell, - cap on the 2.0 mm underside pad, + to the underside rim pad.",
    "- Program before fitting the cell: the programmer drives 3.3 V into VCC.",
]
