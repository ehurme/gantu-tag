"""IN100 insect tag v7: 7 mm round tag, wire antenna, cut-to-start tail, any 1.4-1.55 V button cell,
and a mixed-variant test panel.

Tag coordinates: origin at the centre of the round tag (and of the cell under it), x right, y down (top view), mm.

What's new in v7 (after a part-by-part check against SparkFun's NanoBeacon boards and the IN100 datasheet):
  - C4, a 0402 decoupler right at the VCC pin (SparkFun: 100 nF + 10 uF; v6 had only the 47 uF).
  - C2, the CHIP_EN delay capacitor, moved from the tail onto the tag, so EN rises after VCC however the cell
    goes on (datasheet power-up order), as on SparkFun's boards (1 k / 100 nF there).
  - Four vias in the IN100's exposed pad (datasheet: at least four).
  - Battery-agnostic cell interface: a + pad on the top rim (wire over the edge to the can's side wall) instead
    of v6's plated hole, which would sit over the negative cap of a large cell; a smaller (1.6 mm) negative pad;
    underside centring rings for 4.8 and 5.8 mm cells.
  - AE2: an optional plated hole on GND for a counterpoise wire (try a dipole against the plain monopole).
  - Panel: zones are refilled after the break-tab holes are drilled (v6's holes cut into the ground pour).
  - VARIANTS: five population options built on the same board, mixed on one panel (tools/variants.py).
"""

PROJECT = "insect_tag"

# ---------------------------------------------------------------- parts (values = variant A, the baseline)
PARTS = [
    dict(ref="U1", sym="insect_tag:IN100_QFN18", value="IN100-Q1-R-RC1I",
         fp="insect_tag:InPlay_IN100_QFN-18-1EP_3x3mm_P0.4mm_EP1.5x1.7mm",
         fields={"MPN": "IN100-Q1-R-RC1I", "Manufacturer": "InPlay", "LCSC": "C6062024"},
         sch=(118, 76, 0), pcb=(0.1, 1.45, 0, "F"),
         ref_at=(-11, -10, "left"), val_at=(3, 16, "left")),
    dict(ref="Y1", sym="Device:Crystal_GND24", value="26MHz 7pF",
         fp="insect_tag:Crystal_SMD_1612-4Pin_1.6x1.2mm",
         fields={"MPN": "8Q26000008", "Manufacturer": "TXC", "LCSC": "C5203638"},
         sch=(80, 74, 0), pcb=(-2.43, 0.25, 90, "F"),
         ref_at=(2.5, -3, "left"), val_at=(2.5, 3.5, "left")),
    dict(ref="C1", sym="Device:C", value="47uF 6.3V",
         fp="insect_tag:C_0603_1608Metric",
         fields={"MPN": "GRM188R60J476ME15D", "Manufacturer": "Murata", "LCSC": "C140782"},
         sch=(146, 98, 0), pcb=(1.3, -1.6, 0, "F")),
    dict(ref="C4", sym="Device:C", value="100nF",
         fp="insect_tag:C_0402_1005Metric",
         fields={"MPN": "CL05B104KO5NNNC", "Manufacturer": "Samsung", "LCSC": "C1525",
                 "Note": "At the VCC pin. Variants B and E: 22 uF (C105226)"},
         sch=(160, 98, 0), pcb=(1.35, -0.45, 0, "F")),
    dict(ref="R1", sym="Device:R", value="1M",
         fp="insect_tag:R_0402_1005Metric",
         fields={"MPN": "0402WGF1004TCE", "Manufacturer": "UNI-ROYAL", "LCSC": "C26083",
                 "Note": "CHIP_EN pull-up. Variants C and E: 100k (C25741); D: 10M (C138067)"},
         sch=(100, 56, 0), pcb=(-1.05, -1.05, 90, "F")),
    dict(ref="C2", sym="Device:C", value="10nF",
         fp="insect_tag:C_0402_1005Metric",
         fields={"MPN": "CL05B103KB5NNNC", "Manufacturer": "Samsung", "LCSC": "C15195",
                 "Note": "CHIP_EN delay. Variants C and E: 100 nF (C1525)"},
         sch=(88, 56, 0), pcb=(-1.8, -1.5, 90, "F")),
    dict(ref="JP1", sym="Jumper:SolderJumper_2_Open", value="OFF",
         fp="insect_tag:SolderJumper_OFF_Tail",
         fields={"Note": "Bridge after programming to hold the tag off until the tail is cut"},
         sch=(92, 118, 0), pcb=(-0.8, 11.0, 0, "F"), in_bom=False),
    dict(ref="AE1", sym="Device:Antenna", value="Wire 30mm",
         fp="insect_tag:Antenna_WirePad_THT_D0.8mm_Drill0.4mm",
         fields={"Note": "Builder fits ~30 mm of fine enamelled wire (quarter wave at 2.44 GHz); trim to tune"},
         sch=(150, 52, 0), pcb=(2.75, -0.05, 20, "F"), in_bom=False),
    dict(ref="AE2", sym="Device:Antenna", value="Counterpoise (optional)",
         fp="insect_tag:Antenna_WirePad_THT_D0.8mm_Drill0.4mm",
         fields={"Note": "Optional ~30 mm GND wire, leaving opposite AE1, to make a dipole"},
         sch=(166, 52, 0), pcb=(-2.25, 1.8, 200, "F"), in_bom=False),
    dict(ref="BT1", sym="Device:Battery_Cell", value="337 / 379 / 364 / 377 / ZnAir 10 / 312",
         fp="insect_tag:Cell_Button_EpoxyPad_PlusRim",
         fields={"Note": "Fitted by the builder: - cap silver-epoxied to the underside pad, + wire from the top rim pad"},
         sch=(176, 98, 0), pcb=(0.0, 0.0, 0, "F"), in_bom=False),
    dict(ref="J1", sym="Connector_Generic:Conn_01x04", value="PROG",
         fp="insect_tag:ProgPads_2x02_P2.54mm_THT_Tab",
         fields={"Note": "2 x 2 plated pads on the cut-off tail: R(XD) T(XD) / G +"},
         sch=(70, 110, 0), pcb=(0.0, 8.07, 0, "F"), in_bom=False, mirror="x",
         ref_at=(2, -5, "left"), val_at=(2, 3.5, "left")),
]

# U1 (QFN18): 1 XO_N, 2 XO_P, 3 MGPIO7, 4 MGPIO6, 5 MGPIO5, 6 SW0, 7 SW1, 8 GPIO0 (UART RXD), 9 GPIO1 (UART TXD),
# 10 GPIO2, 11 GPIO3, 12 MGPIO4, 13 VDDQ, 14 RTC_XO_P, 15 RTC_XO_N, 16 RF_TX, 17 VCC, 18 CHIP_EN, 19 EP/GND
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
NO_CONNECT = [("U1", n) for n in ("3", "4", "5", "6", "7", "10", "11", "12", "14", "15")]   # RTC pins: internal 32 kHz RC
POWER_NETS = {"VCC", "GND"}
FLAG_AT = (40, 95)

# ---------------------------------------------------------------- variants (population only; the copper is identical)
# ref -> (value, LCSC, MPN, manufacturer); anything not listed keeps the PARTS value.
V_22U = ("22uF 6.3V", "C105226", "CL05A226MQ5QUNC", "Samsung")
V_100K = ("100k", "C25741", "0402WGF1003TCE", "UNI-ROYAL")
V_100N = ("100nF", "C1525", "CL05B104KO5NNNC", "Samsung")
V_10M = ("10M", "C138067", "RC0402FR-0710ML", "YAGEO")
VARIANTS = {
    "A": dict(title="Baseline", change={},
              why="47 uF + 100 nF, 1 Mohm / 10 nF enable. The design as intended."),
    "B": dict(title="More bulk", change={"C4": V_22U},
              why="C4 = 22 uF instead of 100 nF (~69 uF in total): margin if TX current at 1.5 V is above the 3 V figure, or for +5 dBm."),
    "C": dict(title="Strong enable", change={"R1": V_100K, "C2": V_100N},
              why="100 k / 100 nF enable, closer to SparkFun's 1 k / 100 nF: tells you whether a 1 Mohm pull-up is too weak. "
                  "Draws 15 uA while the OFF jumper is bridged, so bridge it only just before deployment."),
    "D": dict(title="Low storage drain", change={"R1": V_10M},
              why="10 Mohm pull-up: 0.15 uA while the OFF jumper is bridged (v6's 1 Mohm: 1.5 uA). Tells you whether the IN100's "
                  "CHIP_EN starts reliably through 10 Mohm."),
    "E": dict(title="Belt and braces", change={"C4": V_22U, "R1": V_100K, "C2": V_100N},
              why="B and C together: the variant most likely to work if anything marginal is going on."),
}
# Panel columns (left to right on the unrotated top row) -> variant; the turned bottom row mirrors left/right.
PANEL_COLUMNS = ["A", "A", "B", "B", "C", "C", "D", "D", "E", "E"]

# ---------------------------------------------------------------- outline
R_TAG = 3.5
NECK_X0, NECK_X1, NECK_Y0, NECK_Y1 = -0.9, 0.9, 2.6, 4.9      # 1.8 mm neck: cut here to start the tag
TAB_X0, TAB_X1, TAB_Y0, TAB_Y1 = -3.0, 3.0, 4.9, 12.2         # programming tail
CUT_Y = 3.95                                                  # silkscreen cut line across the neck
PLUS_PAD = (0.8, -2.7)         # top-side rim pad for the + wire (VCC via inside it)
PLUS_PAD_SIZE = (0.9, 0.6)
NEG_PAD_D = 1.6                # gold pad on the underside for the cell's negative cap (silver epoxy)
CELL_RINGS = (2.45, 2.95)      # underside centring rings: 4.8 mm (337) and 5.8 mm (379, ZnAir 10) cells


def outline_polygon():
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
    return unary_union([Point(0, 0).buffer(R_TAG, 256),
                        box(NECK_X0, NECK_Y0, NECK_X1, NECK_Y1),
                        box(TAB_X0, TAB_Y0, TAB_X1, TAB_Y1)])


def pour_polygon():
    """GND pour area on both layers: the round tag only (not the neck or tail)."""
    from shapely.geometry import Point
    return Point(0, 0).buffer(R_TAG, 128)


# KiKit tab annotations (just outside an edge, arrow pointing in). Rows alternate by 180 deg about the unit's
# bounding-box centre (x = 0), so the tail-bottom tab at x = 0 meets its mate on the turned row.
# The top tab (to the rail) is off-centre, away from the + pad.
_KT1_X = -0.7
BOARD_ONLY = [
    dict(ref="KT1", fp="insect_tag:KiKit_Tab_1p0mm",
         pcb=(_KT1_X, -((R_TAG ** 2 - (abs(_KT1_X) - 0.5) ** 2) ** 0.5 + 0.05), 270, "F")),   # tag top -> rail
    dict(ref="KT2", fp="insect_tag:KiKit_Tab_1p0mm", pcb=(-(R_TAG + 0.04), 0.5, 0, "F")),         # tag left
    dict(ref="KT3", fp="insect_tag:KiKit_Tab_1p0mm", pcb=(R_TAG + 0.04, 0.5, 180, "F")),          # tag right (mates KT2)
    dict(ref="KT4", fp="insect_tag:KiKit_Tab_1p2mm", pcb=(0.0, TAB_Y1 + 0.05, 90, "F")),          # tail bottom
]

# ---------------------------------------------------------------- routing (all hand-placed)
VIA_D, VIA_DRILL = 0.5, 0.3
ZONE_CLEARANCE = 0.15
W_SIG, W_XO, W_PWR, W_RF = 0.13, 0.15, 0.2, 0.25
UX, UY = 0.1, 1.45       # U1 centre
V_EN = (-0.35, -1.2)     # CHIP_EN to the underside (clear of the negative pad)
V_VCC = (-0.35, -2.35)   # VCC to the underside, kept 0.9 mm inside the edge so the right-hand ground crescent stays joined
V_DQ = (2.45, UY)        # VDDQ to the underside VCC track
X_RXD, X_TXD = -0.5, 0.5                   # neck lanes, top layer
X_GND_B, X_EN_B, X_VCC_B = -0.5, 0.0, 0.5  # neck lanes, bottom layer (EN sits between GND and VCC)
X_GND_TAIL, Y_GND_TAIL = -2.45, 5.25       # bottom GND lane: round the outside of the R pad to G
X_EN_TAIL, X_VCC_TAIL = -0.25, 0.3         # lanes inside the tail, clear of the pads
V_EN_TAIL = (0.0, 10.1)                   # CHIP_EN back to the top at the OFF jumper
EP_VIAS = [(UX + dx, UY + dy) for dx in (-0.4, 0.4) for dy in (-0.45, 0.45)]


def static_tracks():
    # Crystal: XO_P straight across into pad 1; XO_N through the gap between the crystal's pad rows to pad 3.
    yield ("XO_P", "F", W_XO, [("U1", "2"), ("Y1", "1")])
    yield ("XO_N", "F", W_XO, [("U1", "1"), (-2.8, UY - 1.2), ("Y1", "3")])
    # RF straight to the antenna hole.
    yield ("RF", "F", W_RF, [("U1", "16"), ("AE1", "1")])
    # VCC top: pin 17 straight up through C4's pad to C1; C1 to the + pad; R1 over to C1; VDDQ to its via.
    yield ("VCC", "F", W_PWR, [("U1", "17"), (0.35, -0.45), (0.35, -1.6), ("C1", "1")])
    yield ("VCC", "F", W_PWR, [(0.35, -0.45), ("C4", "1")])
    yield ("VCC", "F", W_PWR, [("C1", "1"), PLUS_PAD])
    yield ("VCC", "F", W_PWR, [("R1", "2"), (-1.05, -1.95), (0.1, -1.95)])
    yield ("VCC", "F", W_PWR, [(-0.35, -1.95), V_VCC])
    yield ("VCC", "F", W_PWR, [("U1", "13"), V_DQ])
    # CHIP_EN: pin 18 up to its via; R1 and C2 hang off it.
    yield ("EN", "F", W_SIG, [("U1", "18"), (-0.15, -0.55), V_EN])
    yield ("EN", "F", W_SIG, [(-0.15, -0.55), (-0.6, -0.55), ("R1", "1")])
    yield ("EN", "F", W_SIG, [("R1", "1"), ("C2", "1")])
    # Underside: CHIP_EN and VCC run side by side down the right of the cell pad and into the neck.
    yield ("EN", "B", W_SIG, [V_EN, (0.6, -1.2), (1.0, -1.0), (1.3, -0.6), (1.3, 2.0), (X_EN_B, 3.0),
                              (X_EN_B, 5.9), (X_EN_TAIL, 6.15), (X_EN_TAIL, 9.85), V_EN_TAIL])
    yield ("VCC", "B", W_PWR, [V_VCC, (1.0, -2.35), (1.7, -1.6), (1.7, 2.3), (X_VCC_B, 3.1),
                               (X_VCC_B, 5.9), (X_VCC_TAIL, 6.1), (X_VCC_TAIL, 8.5), ("J1", "4")])
    yield ("VCC", "B", W_PWR, [V_DQ, (1.7, UY)])
    # GND top: crystal lid pad 4 to the counterpoise hole (which doubles as its via).
    yield ("GND", "F", W_PWR, [("Y1", "4"), ("AE2", "1")])
    # UART on top through the neck; GND starts in the underside pour and runs down the bottom of the neck.
    yield ("RXD", "F", W_SIG, [("U1", "8"), (-0.15, 3.25), (X_RXD, 3.55), (X_RXD, 6.0), ("J1", "3")])
    yield ("TXD", "F", W_SIG, [("U1", "9"), (0.35, 3.25), (X_TXD, 3.4), (X_TXD, 6.0), ("J1", "2")])
    yield ("GND", "B", W_PWR, [(X_GND_B, 2.3), (X_GND_B, Y_GND_TAIL), (-1.9, Y_GND_TAIL), (X_GND_TAIL, 5.8),
                               (X_GND_TAIL, 8.9), ("J1", "1")])
    # Tail: the OFF jumper.
    yield ("EN", "F", W_SIG, [V_EN_TAIL, ("JP1", "1")])
    yield ("GND", "F", W_PWR, [("JP1", "2"), ("J1", "1")])


def static_vias():
    yield ("EN",) + V_EN
    yield ("VCC",) + V_VCC
    yield ("VCC",) + V_DQ
    yield ("EN",) + V_EN_TAIL
    for x, y in EP_VIAS:          # exposed-pad vias (datasheet: at least four)
        yield ("GND", round(x, 3), round(y, 3))
    yield ("GND", -2.5, -1.0)     # stitches the top pour by the crystal and C2
    yield ("GND", 2.7, 0.75)      # stitches the top pour between RF and VDDQ
    yield ("GND", 2.8, -0.95)     # C1 and C4 ground


# Silkscreen (text, x, y, size, side, angle) and lines ((x1, y1), (x2, y2), side)
SILK_TEXT = [("CUT", 0.0, 4.45, 0.42, "F", 0),
             ("R", -2.45, 6.8, 0.6, "F", 0), ("T", 2.45, 6.8, 0.6, "F", 0),
             ("G", -2.45, 9.34, 0.6, "F", 0), ("+", 2.45, 9.34, 0.6, "F", 0),
             ("OFF", 1.0, 11.0, 0.6, "F", 0),
             ("+", 1.55, -2.55, 0.45, "F", 0),
             ("A", 2.4, 11.0, 0.8, "F", 0)]      # variant letter (tools/variants.py rewrites it per panel column)
SILK_LINES = [((NECK_X0, CUT_Y), (NECK_X1, CUT_Y), "F")]
