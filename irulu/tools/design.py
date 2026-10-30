"""IN100 insect tag v6: 7 mm round tag, wire antenna, cut-to-start tail (Blu Bat style).

Tag coordinates: origin at the centre of the round tag (and of the cell under it), x right, y down (top view), mm.

What's new in v6:
  - Cut-to-start: CHIP_EN has a 1 Mohm pull-up on the tag and runs down the tail. After programming, a solder
    bridge on the tail ("OFF") holds CHIP_EN low: the IN100 then draws ~10 nA plus 1.5 uA in the pull-up, with
    the cell fitted. Cutting the tail removes the bridge, CHIP_EN rises (after VCC, as the datasheet's
    power-up sequence requires) and the tag starts. Without the bridge, the tag starts as soon as the cell is fitted.
  - One 47 uF 0603 bulk capacitor (sized for a few weeks at 0 dBm on the first half of a 337 cell).
  - IN100 pushed toward the tail; crystal on the left beside the XO pins, the capacitor, pull-up and + hole above.
  - Cell: negative cap silver-epoxied to a gold pad on the underside; + by a thin wire into a plated hole.
"""

PROJECT = "insect_tag"

# ---------------------------------------------------------------- parts
PARTS = [
    dict(ref="U1", sym="insect_tag:IN100_QFN18", value="IN100-Q1-R-RC1I",
         fp="insect_tag:InPlay_IN100_QFN-18-1EP_3x3mm_P0.4mm_EP1.5x1.7mm",
         fields={"MPN": "IN100-Q1-R-RC1I", "Manufacturer": "InPlay", "LCSC": "C6062024"},
         sch=(118, 76, 0), pcb=(0.1, 1.1, 0, "F"),
         ref_at=(-11, -10, "left"), val_at=(3, 16, "left")),
    dict(ref="Y1", sym="Device:Crystal_GND24", value="26MHz 7pF",
         fp="insect_tag:Crystal_SMD_1612-4Pin_1.6x1.2mm",
         fields={"MPN": "8Q26000008", "Manufacturer": "TXC", "LCSC": "C5203638"},
         sch=(80, 74, 0), pcb=(-2.425, -0.1, 90, "F"),
         ref_at=(2.5, -3, "left"), val_at=(2.5, 3.5, "left")),
    dict(ref="C1", sym="Device:C", value="47uF 6.3V",
         fp="insect_tag:C_0603_1608Metric",
         fields={"MPN": "GRM188R60J476ME15D", "Manufacturer": "Murata", "LCSC": "C140782"},
         sch=(146, 98, 0), pcb=(1.4, -1.4, 0, "F")),
    dict(ref="R1", sym="Device:R", value="1M",
         fp="insect_tag:R_0402_1005Metric",
         fields={"MPN": "0402WGF1004TCE", "Manufacturer": "UNI-ROYAL", "LCSC": "C26083"},
         sch=(100, 56, 0), pcb=(-0.3, -1.6, 90, "F")),
    dict(ref="C2", sym="Device:C", value="10nF",
         fp="insect_tag:C_0402_1005Metric",
         fields={"MPN": "CL05B103KB5NNNC", "Manufacturer": "Samsung", "LCSC": "C15195",
                 "Note": "On the cut-off tail: delays CHIP_EN during programming"},
         sch=(108, 116, 0), pcb=(-0.8, 12.0, 180, "F")),
    dict(ref="JP1", sym="Jumper:SolderJumper_2_Open", value="OFF",
         fp="insect_tag:SolderJumper_OFF_Tail",
         fields={"Note": "Bridge after programming to hold the tag off until the tail is cut"},
         sch=(92, 118, 0), pcb=(-0.8, 11.0, 0, "F"), in_bom=False),
    dict(ref="AE1", sym="Device:Antenna", value="Wire 30mm",
         fp="insect_tag:Antenna_WirePad_THT_D0.8mm_Drill0.4mm",
         fields={"Note": "Builder fits ~30 mm of fine enamelled wire (quarter wave at 2.44 GHz); trim to tune"},
         sch=(150, 52, 0), pcb=(2.75, -0.4, 20, "F"), in_bom=False),
    dict(ref="BT1", sym="Device:Battery_Cell", value="337 SR416SW",
         fp="insect_tag:Cell_337_EpoxyPad_PlusHole",
         fields={"MPN": "SR416SW", "Note": "Fitted by the builder: - cap silver-epoxied to the underside pad, + wire in the hole"},
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
    "VCC":  [("U1", "17"), ("U1", "13"), ("C1", "1"), ("R1", "2"), ("BT1", "1"), ("J1", "4")],
    "GND":  [("U1", "19"), ("Y1", "2"), ("Y1", "4"), ("C1", "2"), ("C2", "2"), ("JP1", "2"), ("BT1", "2"), ("J1", "1")],
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

# ---------------------------------------------------------------- outline
R_TAG = 3.5
NECK_X0, NECK_X1, NECK_Y0, NECK_Y1 = -0.9, 0.9, 2.6, 4.9      # 1.8 mm neck: cut here to start the tag
TAB_X0, TAB_X1, TAB_Y0, TAB_Y1 = -3.0, 3.0, 4.9, 12.7         # programming tail
CUT_Y = 3.9                                                   # silkscreen cut line across the neck
PLUS_HOLE = (0.45, -2.5)       # plated hole for the + wire from the cell's can (also the VCC via)
NEG_PAD_D = 2.0                # gold pad on the underside for the cell's negative cap (silver epoxy)


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
BOARD_ONLY = [
    dict(ref="KT1", fp="insect_tag:KiKit_Tab_1p0mm", pcb=(0.0, -(R_TAG + 0.05), 270, "F")),       # tag top -> rail
    dict(ref="KT2", fp="insect_tag:KiKit_Tab_1p0mm", pcb=(-(R_TAG + 0.04), 0.5, 0, "F")),         # tag left
    dict(ref="KT3", fp="insect_tag:KiKit_Tab_1p0mm", pcb=(R_TAG + 0.04, 0.5, 180, "F")),          # tag right (mates KT2)
    dict(ref="KT4", fp="insect_tag:KiKit_Tab_1p2mm", pcb=(0.0, TAB_Y1 + 0.05, 90, "F")),          # tail bottom
]

# ---------------------------------------------------------------- routing (all hand-placed)
VIA_D, VIA_DRILL = 0.5, 0.3
ZONE_CLEARANCE = 0.15
W_SIG, W_XO, W_PWR, W_RF = 0.13, 0.15, 0.2, 0.25
V_EN = (-0.95, -1.15)    # CHIP_EN to the underside
V_DQ = (2.45, 1.1)       # VDDQ to the underside VCC track
X_RXD, X_TXD = -0.5, 0.5                   # neck lanes, top layer
X_GND_B, X_EN_B, X_VCC_B = -0.5, 0.0, 0.5  # neck lanes, bottom layer (EN sits between GND and VCC)
X_GND_TAIL, Y_GND_TAIL = -2.45, 5.25       # bottom GND lane: round the outside of the R pad to G
X_EN_TAIL, X_VCC_TAIL = -0.25, 0.3         # lanes inside the tail, clear of the pads
V_EN_TAIL = (0.0, 10.1)                   # CHIP_EN back to the top at the OFF jumper


def static_tracks():
    # Crystal: XO_P straight across into pad 1; XO_N through the gap between the crystal's pad rows to pad 3.
    yield ("XO_P", "F", W_XO, [("U1", "2"), ("Y1", "1")])
    yield ("XO_N", "F", W_XO, [("U1", "1"), (-2.8, -0.1), ("Y1", "3")])
    # RF straight to the antenna hole.
    yield ("RF", "F", W_RF, [("U1", "16"), ("AE1", "1")])
    # VCC top: pin 17 up to C1; C1, R1 and the + hole joined; VDDQ to its via.
    yield ("VCC", "F", W_PWR, [("U1", "17"), ("C1", "1")])
    yield ("VCC", "F", W_PWR, [("C1", "1"), (0.45, -1.95), PLUS_HOLE])
    yield ("VCC", "F", W_PWR, [("R1", "2"), PLUS_HOLE])
    yield ("VCC", "F", W_PWR, [("U1", "13"), V_DQ])
    # CHIP_EN: pin 18 up to the pull-up and its via.
    yield ("EN", "F", W_SIG, [("U1", "18"), ("R1", "1")])
    yield ("EN", "F", W_SIG, [("R1", "1"), V_EN])
    # Underside: CHIP_EN and VCC run side by side down the right of the cell pad and into the neck.
    yield ("EN", "B", W_SIG, [V_EN, (0.0, -1.35), (1.0, -1.0), (1.35, -0.5), (1.35, 2.0), (X_EN_B, 3.0),
                              (X_EN_B, 5.9), (X_EN_TAIL, 6.15), (X_EN_TAIL, 9.85), V_EN_TAIL])
    yield ("VCC", "B", W_PWR, [PLUS_HOLE, (1.5, -2.0), (1.85, -1.2), (1.85, 2.0), (X_VCC_B, 3.1),
                               (X_VCC_B, 5.9), (X_VCC_TAIL, 6.1), (X_VCC_TAIL, 8.5), ("J1", "4")])
    yield ("VCC", "B", W_PWR, [V_DQ, (1.85, 1.1)])
    # GND top: crystal lid pads and C1 to vias.
    yield ("GND", "F", W_PWR, [("Y1", "2"), (-1.75, -1.2)])
    yield ("GND", "F", W_PWR, [("Y1", "4"), (-2.55, 1.15)])
    yield ("GND", "F", W_PWR, [("C1", "2"), (1.95, -2.3)])
    # UART on top through the neck; GND starts in the underside pour and runs down the bottom of the neck.
    yield ("RXD", "F", W_SIG, [("U1", "8"), (-0.15, 2.95), (X_RXD, 3.15), (X_RXD, 6.0), ("J1", "3")])
    yield ("TXD", "F", W_SIG, [("U1", "9"), (0.35, 2.95), (X_TXD, 3.1), (X_TXD, 6.0), ("J1", "2")])
    yield ("GND", "B", W_PWR, [(X_GND_B, 2.4), (X_GND_B, Y_GND_TAIL), (-1.9, Y_GND_TAIL), (X_GND_TAIL, 5.8),
                               (X_GND_TAIL, 8.9), ("J1", "1")])
    # Tail: OFF jumper and the 10 nF CHIP_EN capacitor.
    yield ("EN", "F", W_SIG, [V_EN_TAIL, ("JP1", "1")])
    yield ("EN", "F", W_SIG, [("JP1", "1"), ("C2", "1")])
    yield ("GND", "F", W_PWR, [("JP1", "2"), ("J1", "1")])
    yield ("GND", "F", W_PWR, [("JP1", "2"), ("C2", "2")])


def static_vias():
    yield ("EN",) + V_EN
    yield ("VCC",) + V_DQ
    yield ("EN",) + V_EN_TAIL
    yield ("GND", -0.3, 1.55)     # exposed-pad vias
    yield ("GND", 0.5, 1.55)
    yield ("GND", -1.75, -1.2)    # crystal pad 2
    yield ("GND", -2.55, 1.15)    # crystal pad 4
    yield ("GND", 1.95, -2.3)     # C1 ground
    yield ("GND", 2.7, 0.45)      # stitches the top pour between RF and VDDQ


# Silkscreen (text, x, y, size, side, angle) and lines ((x1, y1), (x2, y2), side)
SILK_TEXT = [("CUT", 0.0, 4.4, 0.42, "F", 0),
             ("R", -2.45, 6.8, 0.6, "F", 0), ("T", 2.45, 6.8, 0.6, "F", 0),
             ("G", -2.45, 9.34, 0.6, "F", 0), ("+", 2.45, 9.34, 0.6, "F", 0),
             ("OFF", 1.0, 11.0, 0.6, "F", 0)]
SILK_LINES = [((NECK_X0, CUT_Y), (NECK_X1, CUT_Y), "F")]
