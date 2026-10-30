"""IN100 insect tag v5: 8 mm round tag, wire antenna, cut-off programming tab.

Tag coordinates: origin at the centre of the round tag, x right, y down (top view), mm. build.py adds an offset.

Changes from v4:
  - IN100 in QFN18 (IN100-Q1-R-RC1I, LCSC C6062024), the package JLC stocks, so the order is fully turnkey.
  - Bulk capacitance sized for the 337 silver-oxide cell: about 80 ohm internal resistance (Energizer datasheet:
    75-85 ohm at 40 Hz) against 9.1-13.8 mA TX bursts (IN100 datasheet). One 100 uF 0805 keeps the supply above
    1.2 V through an advertising event even at 250 ohm (cold or nearly flat cell), at 0 dBm and +5 dBm.
    See tools/burst_sim.py.
  - Wire antenna in a plated hole instead of the printed arm: lighter, flexible, and 20 tags per panel instead of 12.
  - Own 3D models for every part (insect_tag.3dshapes), so KiCad's 3D viewer shows the whole tag.

Layout (top view): U1 in the middle; crystal at the upper left beside the XO pins; 100 nF and the + rim pad
at the top; the antenna hole at the upper right beside RF_TX; the 100 uF cap at 45 deg at the lower left;
- rim pad at the right; the neck and programming tab below (UART pins face down).
"""

PROJECT = "insect_tag"
LCSC_IN100 = "C6062024"

# ---------------------------------------------------------------- parts
PARTS = [
    dict(ref="U1", sym="insect_tag:IN100_QFN18", value="IN100-Q1-R-RC1I",
         fp="insect_tag:InPlay_IN100_QFN-18-1EP_3x3mm_P0.4mm_EP1.5x1.7mm",
         fields={"MPN": "IN100-Q1-R-RC1I", "Manufacturer": "InPlay", "LCSC": LCSC_IN100},
         sch=(118, 76, 0), pcb=(0.45, 0.15, 0, "F"),
         ref_at=(-11, -10, "left"), val_at=(3, 16, "left")),
    dict(ref="Y1", sym="Device:Crystal_GND24", value="26MHz 7pF",
         fp="insect_tag:Crystal_SMD_1612-4Pin_1.6x1.2mm",
         fields={"MPN": "8Q26000008", "Manufacturer": "TXC", "LCSC": "C5203638"},
         sch=(80, 74, 0), pcb=(-2.075, -1.05, 90, "F"),
         ref_at=(2.5, -3, "left"), val_at=(2.5, 3.5, "left")),
    dict(ref="C1", sym="Device:C", value="100nF",
         fp="insect_tag:C_0402_1005Metric",
         fields={"MPN": "CL05B104KO5NNNC", "Manufacturer": "Samsung", "LCSC": "C1525"},
         sch=(146, 98, 0), pcb=(0.85, -2.15, 0, "F")),
    dict(ref="C2", sym="Device:C", value="100uF 6.3V",
         fp="insect_tag:C_0805_2012Metric",
         fields={"MPN": "GRM21BR60J107ME15L", "Manufacturer": "Murata", "LCSC": "C141660"},
         sch=(160, 98, 0), pcb=(-1.99, 1.99, 315, "F")),
    dict(ref="AE1", sym="Device:Antenna", value="Wire 30mm",
         fp="insect_tag:Antenna_WirePad_THT_D0.8mm_Drill0.4mm",
         fields={"Note": "Builder fits ~30 mm of fine enamelled wire (quarter wave at 2.44 GHz); trim to tune"},
         sch=(150, 52, 0), pcb=(2.6, -1.45, 30, "F"), in_bom=False),
    dict(ref="BT1", sym="Device:Battery_Cell", value="337 SR416SW",
         fp="insect_tag:Cell_337_TopTabPads",
         fields={"MPN": "SR416SW", "Note": "Fitted by the builder: cell under the tag on Kapton, welded tabs onto the rim pads"},
         sch=(176, 98, 0), pcb=(0.0, 0.0, 0, "F"), in_bom=False),
    dict(ref="J1", sym="Connector_Generic:Conn_01x04", value="PROG",
         fp="insect_tag:ProgPads_2x02_P2.54mm_THT_Tab",
         fields={"Note": "2 x 2 plated pads on the cut-off tab: R(XD) T(XD) / + G"},
         sch=(70, 110, 0), pcb=(0.45, 8.57, 0, "F"), in_bom=False, mirror="x",
         ref_at=(2, -5, "left"), val_at=(2, 3.5, "left")),
]

# U1 (QFN18) pins: 1 XO_N, 2 XO_P, 3 MGPIO7, 4 MGPIO6, 5 MGPIO5, 6 SW0, 7 SW1, 8 GPIO0 (UART RXD), 9 GPIO1 (UART TXD),
# 10 GPIO2, 11 GPIO3, 12 MGPIO4, 13 VDDQ, 14 RTC_XO_P, 15 RTC_XO_N, 16 RF_TX, 17 VCC, 18 CHIP_EN, 19 EP/GND
NETS = {
    "VCC":  [("U1", "17"), ("U1", "18"), ("U1", "13"), ("C1", "1"), ("C2", "1"), ("BT1", "1"), ("J1", "4")],
    "GND":  [("U1", "19"), ("Y1", "2"), ("Y1", "4"), ("C1", "2"), ("C2", "2"), ("BT1", "2"), ("J1", "1")],
    "XO_N": [("U1", "1"), ("Y1", "3")],
    "XO_P": [("U1", "2"), ("Y1", "1")],
    "TXD":  [("U1", "9"), ("J1", "2")],
    "RXD":  [("U1", "8"), ("J1", "3")],
    "RF":   [("U1", "16"), ("AE1", "1")],
}
NO_CONNECT = [("U1", n) for n in ("3", "4", "5", "6", "7", "10", "11", "12", "14", "15")]   # RTC pins: internal 32 kHz RC
POWER_NETS = {"VCC", "GND"}
FLAG_AT = (40, 95)

# ---------------------------------------------------------------- outline
R_TAG = 4.0
NECK_X0, NECK_X1, NECK_Y0, NECK_Y1 = -0.45, 1.35, 2.8, 5.6     # 1.8 mm neck, cut after programming
TAB_X0, TAB_X1, TAB_Y0, TAB_Y1 = -1.95, 2.85, 5.6, 11.5        # programming tab
CUT_Y = 4.25                                                    # silkscreen cut line across the neck
BT_PADS = {"1": (-0.35, -3.0), "2": (2.85, 1.1)}                # rim pads for the cell tabs: + top, - right
BT_PAD_D = 0.7
BT_NEG_D = 2.0      # bare gold pad on the underside, centred on the cell's negative cap (silver-epoxy option)


def outline_polygon():
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
    return unary_union([Point(0, 0).buffer(R_TAG, 256),
                        box(NECK_X0, NECK_Y0, NECK_X1, NECK_Y1),
                        box(TAB_X0, TAB_Y0, TAB_X1, TAB_Y1)])


def pour_polygon():
    """GND pour area on both layers: the round tag only (not the neck or tab)."""
    from shapely.geometry import Point
    return Point(0, 0).buffer(R_TAG, 128)


# KiKit tab annotations, just outside an edge, arrow pointing into the board. The panel turns every second row
# by 180 deg about the unit's bounding-box centre (x = 0), so the tab-bottom annotation sits at x = 0 to meet
# its mate on the turned row.
_xt = 1.5
BOARD_ONLY = [
    # tag top -> rail; the annotation must clear the curved edge across the whole 1 mm tab width
    dict(ref="KT1", fp="insect_tag:KiKit_Tab_1p0mm", pcb=(_xt, -(R_TAG ** 2 - (_xt - 0.5) ** 2) ** 0.5 - 0.05, 270, "F")),
    dict(ref="KT2", fp="insect_tag:KiKit_Tab_1p0mm", pcb=(-(R_TAG + 0.04), -0.5, 0, "F")),                        # tag left
    dict(ref="KT3", fp="insect_tag:KiKit_Tab_1p0mm", pcb=(R_TAG + 0.04, -0.5, 180, "F")),                        # tag right (mates KT2)
    dict(ref="KT4", fp="insect_tag:KiKit_Tab_1p2mm", pcb=(0.0, TAB_Y1 + 0.05, 90, "F")),                         # tab bottom
]

# ---------------------------------------------------------------- routing (all hand-placed)
VIA_D, VIA_DRILL = 0.5, 0.3
ZONE_CLEARANCE = 0.15
W_SIG, W_XO, W_PWR, W_RF = 0.13, 0.15, 0.2, 0.25
V_TOP = (-0.45, -2.15)   # VCC via by C1 and the + pad
V_DQ = (2.7, 0.15)       # VCC via for VDDQ
V_LEFT = (-1.84, 0.5)    # VCC via beside the bulk cap
G_N = (0.45, 2.8)        # GND via feeding the neck's GND lane
X_RXD, X_GND, X_TXD = -0.1, 0.45, 1.0      # neck lanes, top layer
X_VCC_B = -0.1                             # neck lane, bottom layer (VCC alone)
X_VCC_TAB = 0.15                           # VCC lane inside the tab, clear of the RXD pad


def static_tracks():
    # Crystal: XO_P straight across to Y1 pad 1; XO_N through the gap between the crystal's pad rows to pad 3.
    yield ("XO_P", "F", W_XO, [("U1", "2"), (-1.6, -0.65), ("Y1", "1")])
    yield ("XO_N", "F", W_XO, [("U1", "1"), (-2.45, -1.05), ("Y1", "3")])
    # RF straight to the antenna hole.
    yield ("RF", "F", W_RF, [("U1", "16"), ("AE1", "1")])
    # VCC top: CHIP_EN tied to VCC between the pads, up to C1, the top via and the + pad.
    yield ("VCC", "F", W_PWR, [("U1", "18"), ("U1", "17")])
    yield ("VCC", "F", W_PWR, [("U1", "17"), (0.45, -1.75), ("C1", "1")])
    yield ("VCC", "F", W_PWR, [("C1", "1"), V_TOP])
    yield ("VCC", "F", W_PWR, [V_TOP, ("BT1", "1")])
    yield ("VCC", "F", W_PWR, [("U1", "13"), V_DQ])
    # VCC bulk cap (upper-left pad) to the left via.
    yield ("VCC", "F", W_PWR, [("C2", "1"), V_LEFT])
    # VCC bottom spine: top via -> VDDQ via -> under U1 -> neck; left via -> neck. Only the neck reaches the edge.
    yield ("VCC", "B", W_PWR, [V_TOP, (0.0, -1.4), (1.2, -1.4), V_DQ])
    yield ("VCC", "B", W_PWR, [V_DQ, (1.3, 1.55), (1.3, 2.3), (X_VCC_B, 2.3)])
    yield ("VCC", "B", W_PWR, [V_LEFT, (-0.6, 1.9), (X_VCC_B, 2.3)])
    yield ("VCC", "B", W_PWR, [(X_VCC_B, 2.3), (X_VCC_B, 6.3), (X_VCC_TAB, 6.55), (X_VCC_TAB, 9.2), ("J1", "4")])
    # GND top: C1 to its via; crystal ground pads to the bulk caps' ground column and vias; - pad to its via.
    yield ("GND", "F", W_PWR, [("C1", "2"), (1.85, -1.85)])
    yield ("GND", "F", W_PWR, [("Y1", "2"), (-1.5, -2.35)])
    yield ("GND", "F", W_PWR, [("Y1", "4"), (-3.1, -0.4)])
    yield ("GND", "F", W_PWR, [("C2", "2"), (-0.75, 3.1)])
    yield ("GND", "F", W_PWR, [("BT1", "2"), (2.4, 1.9)])
    yield ("GND", "F", W_PWR, [G_N, (X_GND, 9.1), (1.0, 9.84), ("J1", "1")])
    # UART on top through the neck, either side of GND.
    yield ("RXD", "F", W_SIG, [("U1", "8"), (0.2, 2.0), (X_RXD, 2.3), (X_RXD, 6.3), ("J1", "3")])
    yield ("TXD", "F", W_SIG, [("U1", "9"), (0.7, 2.0), (X_TXD, 2.3), (X_TXD, 6.3), ("J1", "2")])


def static_vias():
    yield ("VCC",) + V_TOP
    yield ("VCC",) + V_DQ
    yield ("VCC",) + V_LEFT
    yield ("GND", 0.05, 0.6)      # exposed-pad vias, outside the paste windows
    yield ("GND", 0.85, -0.3)
    yield ("GND", 1.85, -1.85)    # C1 ground
    yield ("GND", -1.5, -2.35)    # crystal pad 2
    yield ("GND", -0.75, 3.1)     # bulk cap ground
    yield ("GND", -3.1, -0.4)     # crystal pad 4
    yield ("GND", 2.4, 1.9)       # - pad
    yield ("GND",) + G_N          # neck GND lane


# Silkscreen (text, x, y, size, side, angle) and lines ((x1, y1), (x2, y2), side)
SILK_TEXT = [("CUT", 0.45, 4.92, 0.6, "F", 0),
             ("R", -0.82, 6.22, 0.6, "F", 0), ("T", 1.72, 6.22, 0.6, "F", 0),
             ("+", -0.82, 10.92, 0.6, "F", 0), ("G", 1.72, 10.92, 0.6, "F", 0)]
SILK_LINES = [((NECK_X0, CUT_Y), (NECK_X1, CUT_Y), "F")]
