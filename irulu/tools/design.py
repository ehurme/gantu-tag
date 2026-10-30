"""IN100 insect tag v4: 6.4 mm round tag, printed antenna arm, cut-off programming tab (Blu Bat-style).

Tag coordinates: origin at the centre of the round tag, x right, y down (top view), mm. build.py adds an offset.

Layout (top view):
  - IN100 (U1) in the middle, rotated 90 deg: top pad row RF, VCC, VDDQ, RXD; bottom row CHIP_EN, XO_N, XO_P, TXD.
  - 26 MHz 1612 crystal (Y1) just below the XO pins; 100 nF (C1) right above the VCC/VDDQ pins;
    10 uF (C2) on the left beside CHIP_EN.
  - The RF pin feeds a quarter-wave trace that runs up a 0.8 mm FR-4 arm leaving the tag at the upper left.
  - A neck on the right carries RXD, GND, TXD (top) and VCC (bottom, alone) to a 2 x 2 pad programming tab.
    The neck is cut after programming.
  - Two rim pads take the 337 cell's welded tabs: + on the left, - at the lower right.
All copper follows JLCPCB's standard 2-layer rules (>= 0.13 mm track and gap, 0.3 mm via drill, >= 0.2 mm to the edge).
"""

PROJECT = "insect_tag"

# ---------------------------------------------------------------- parts
PARTS = [
    dict(ref="U1", sym="insect_tag:IN100", value="IN100-D1-R-YC1I",
         fp="insect_tag:InPlay_IN100_DFN-8-1EP_2.5x2.5mm_P0.5mm_EP1.3x1.9mm",
         fields={"MPN": "IN100-D1-R-YC1I", "Manufacturer": "InPlay",
                 "LCSC": "", "Sourcing": "JLC global sourcing or consigned (Mouser 73-IN100-D1-R-YC1I)"},
         sch=(118, 76, 0), pcb=(0.0, -0.25, 90, "F"),
         ref_at=(-11, -7.5, "left"), val_at=(3, 13, "left")),
    dict(ref="Y1", sym="Device:Crystal_GND24", value="26MHz 7pF",
         fp="insect_tag:Crystal_SMD_1612-4Pin_1.6x1.2mm",
         fields={"MPN": "8Q26000008", "Manufacturer": "TXC", "LCSC": "C5203638"},
         sch=(80, 74, 0), pcb=(-0.25, 2.1, 0, "F"),
         ref_at=(2.5, -3, "left"), val_at=(2.5, 3.5, "left")),
    dict(ref="C1", sym="Device:C", value="100nF",
         fp="Capacitor_SMD:C_0402_1005Metric",
         fields={"MPN": "CL05B104KO5NNNC", "Manufacturer": "Samsung", "LCSC": "C1525"},
         sch=(146, 98, 0), pcb=(0.2, -2.4, 0, "F")),
    dict(ref="C2", sym="Device:C", value="10uF 6.3V",
         fp="Capacitor_SMD:C_0402_1005Metric",
         fields={"MPN": "CL05A106MQ5NUNC", "Manufacturer": "Samsung", "LCSC": "C15525"},
         sch=(156, 98, 0), pcb=(-1.78, 0.5, 90, "F")),
    dict(ref="AE1", sym="Device:Antenna", value="PCB arm",
         fp="insect_tag:Antenna_Arm_Feed",
         fields={"Note": "Printed quarter-wave trace up the 0.8 mm FR-4 arm; trim the arm to tune"},
         sch=(150, 52, 0), pcb=(-2.05, -2.95, 0, "F"), in_bom=False),
    dict(ref="BT1", sym="Device:Battery_Cell", value="337 SR416SW",
         fp="insect_tag:Cell_337_TopTabPads",
         fields={"MPN": "SR416SW", "Note": "Fitted by the builder: cell under the tag on Kapton, welded tabs onto the rim pads"},
         sch=(176, 98, 0), pcb=(0.0, 0.0, 0, "F"), in_bom=False, dnp=True),
    dict(ref="J1", sym="Connector_Generic:Conn_01x04", value="PROG",
         fp="insect_tag:ProgPads_2x02_P2.54mm_THT_Tab",
         fields={"Note": "2 x 2 plated pads on the cut-off tab: R(XD) + / T(XD) G"},
         sch=(70, 110, 0), pcb=(8.0, 0.0, 0, "F"), in_bom=False, mirror="x",
         ref_at=(2, -5, "left"), val_at=(2, 3.5, "left")),
]

# U1 pins: 1 CHIP_EN, 2 XO_N, 3 XO_P, 4 MGPIO5/TXD, 5 MGPIO4/RXD, 6 VDDQ, 7 VCC, 8 RF_TX, 9 EP/GND
NETS = {
    "VCC":  [("U1", "1"), ("U1", "6"), ("U1", "7"), ("C1", "1"), ("C2", "1"), ("BT1", "1"), ("J1", "4")],
    "GND":  [("U1", "9"), ("Y1", "2"), ("Y1", "4"), ("C1", "2"), ("C2", "2"), ("BT1", "2"), ("J1", "1")],
    "XO_N": [("U1", "2"), ("Y1", "1")],
    "XO_P": [("U1", "3"), ("Y1", "3")],
    "TXD":  [("U1", "4"), ("J1", "2")],
    "RXD":  [("U1", "5"), ("J1", "3")],
    "RF":   [("U1", "8"), ("AE1", "1")],
}
POWER_NETS = {"VCC", "GND"}
FLAG_AT = (40, 95)

# ---------------------------------------------------------------- outline
R_TAG = 3.2
ARM_X0, ARM_X1 = -2.45, -1.65          # 0.8 mm wide FR-4 arm carrying the antenna trace
ARM_LEN = 30.0                          # from the tag's top edge to the arm tip
ARM_TIP_Y = -(R_TAG + ARM_LEN)
ARM_CX = (ARM_X0 + ARM_X1) / 2
NECK_X0, NECK_X1, NECK_Y0, NECK_Y1 = 2.5, 5.6, -0.9, 0.9   # 1.8 mm wide neck, cut after programming
TAB_X0, TAB_X1, TAB_Y0, TAB_Y1 = 5.6, 10.4, -2.8, 2.8      # programming tab
CUT_X = 3.45                                                 # silkscreen cut line across the neck
BT_PADS = {"1": (-2.45, 0.95), "2": (1.75, 1.95)}              # rim pads for the cell tabs: + left, - lower right
BT_PAD_D = 0.7


def outline_polygon():
    from shapely.geometry import Point, box
    from shapely.ops import unary_union
    return unary_union([Point(0, 0).buffer(R_TAG, 256),
                        box(ARM_X0, ARM_TIP_Y, ARM_X1, -1.5),
                        box(NECK_X0, NECK_Y0, NECK_X1, NECK_Y1),
                        box(TAB_X0, TAB_Y0, TAB_X1, TAB_Y1)])


def pour_polygon():
    """GND pour area on both layers: the round tag only (not the arm, neck or tab)."""
    from shapely.geometry import Point
    return Point(0, 0).buffer(R_TAG, 128)


# PCB-only footprints: KiKit tab annotations, placed just outside an edge with the arrow pointing into the board.
# The panel (tools/panel.json) alternates rows by 180 deg, so the tag-bottom tab (x 0) and the programming-tab
# bottom tab (x 7.2 = 2 x the unit's bounding-box centre) line up with their mates on the rotated row.
BOARD_ONLY = [
    dict(ref="KT1", fp="insect_tag:KiKit_Tab_0p6mm", pcb=(ARM_CX, ARM_TIP_Y - 0.05, 270, "F")),   # arm tip -> rail
    dict(ref="KT2", fp="insect_tag:KiKit_Tab_1p0mm", pcb=(-3.25, -1.1, 0, "F")),                  # tag left
    dict(ref="KT3", fp="insect_tag:KiKit_Tab_1p0mm", pcb=(TAB_X1 + 0.05, -1.1, 180, "F")),        # tab right (mates KT2)
    dict(ref="KT4", fp="insect_tag:KiKit_Tab_1p2mm", pcb=(0.0, R_TAG + 0.05, 90, "F")),           # tag bottom
    dict(ref="KT5", fp="insect_tag:KiKit_Tab_1p2mm", pcb=(7.2, TAB_Y1 + 0.05, 90, "F")),          # tab bottom
]

# ---------------------------------------------------------------- routing (all hand-placed)
VIA_D, VIA_DRILL = 0.5, 0.3
ZONE_CLEARANCE = 0.15
W_SIG, W_XO, W_PWR, W_RF = 0.13, 0.15, 0.2, 0.25
V_TOP = (-1.05, -2.4)    # VCC via beside C1 (VCC/VDDQ pins)
V_LEFT = (-2.5, -0.45)  # VCC via on the left (CHIP_EN, C2, + pad)
Y_RXD, Y_GND, Y_TXD, Y_VCC_B = -0.55, 0.0, 0.55, -0.3     # neck lanes


def static_tracks():
    # RF: pin 8 left, then diagonally into the arm and up it as the antenna.
    yield ("RF", "F", W_RF, [("U1", "8"), (-1.35, -1.45), (ARM_CX, -2.15), ("AE1", "1")])
    yield ("RF", "F", W_RF, [("AE1", "1"), (ARM_CX, ARM_TIP_Y + 0.5)])
    # Crystal: XO_P straight down; XO_N down the channel between the crystal's pad columns, into pad 1.
    yield ("XO_P", "F", W_XO, [("U1", "3"), ("Y1", "3")])
    yield ("XO_N", "F", W_XO, [("U1", "2"), (-0.25, 2.475), ("Y1", "1")])
    # VCC top: VCC + VDDQ joined, up to C1 and the top via.
    yield ("VCC", "F", W_PWR, [("U1", "6"), ("U1", "7")])
    yield ("VCC", "F", W_PWR, [("U1", "7"), ("C1", "1")])
    yield ("VCC", "F", W_PWR, [V_TOP, ("C1", "1")])
    # VCC left: CHIP_EN - C2 - (+) pad - left via.
    yield ("VCC", "F", W_PWR, [("U1", "1"), ("C2", "1")])
    yield ("VCC", "F", W_PWR, [("C2", "1"), ("BT1", "1")])
    yield ("VCC", "F", W_PWR, [("BT1", "1"), V_LEFT])
    # VCC bottom: top via to left via, and top via out through the neck to the tab's + pad.
    yield ("VCC", "B", W_PWR, [V_TOP, V_LEFT])
    yield ("VCC", "B", W_PWR, [V_TOP, (-0.2, -1.55), (1.65, -1.55), (2.9, Y_VCC_B), (8.4, Y_VCC_B), ("J1", "4")])
    # GND top: C1 to its via; C2 to the exposed pad; crystal ground pads to vias and the (-) pad; EP out to the tab.
    yield ("GND", "F", W_PWR, [("C1", "2"), (1.3, -2.15)])
    yield ("GND", "F", W_PWR, [("C2", "2"), (-0.7, 0.02)])
    yield ("GND", "F", W_PWR, [("Y1", "4"), (-1.5, 1.85)])
    yield ("GND", "F", W_PWR, [("Y1", "2"), ("BT1", "2")])
    yield ("GND", "F", W_PWR, [(0.6, Y_GND), (9.27, Y_GND), ("J1", "1")])
    # UART on top through the neck, either side of GND.
    yield ("RXD", "F", W_SIG, [("U1", "5"), (1.4, -1.45), (2.3, Y_RXD), (5.9, Y_RXD), ("J1", "3")])
    yield ("TXD", "F", W_SIG, [("U1", "4"), (1.4, 0.95), (1.8, Y_TXD), (5.9, Y_TXD), ("J1", "2")])


def static_vias():
    yield ("VCC",) + V_TOP
    yield ("VCC",) + V_LEFT
    yield ("GND", -0.72, -0.25)   # exposed-pad vias, outside the paste opening
    yield ("GND", 0.72, -0.25)
    yield ("GND", 1.3, -2.15)     # C1 ground
    yield ("GND", -1.5, 1.85)     # crystal pad 4
    yield ("GND", 1.1, 2.18)      # crystal pad 2 / (-) pad


# Silkscreen (text, x, y, size, side, angle) and lines ((x1, y1), (x2, y2), side)
SILK_TEXT = [("CUT", 4.55, 0.0, 0.6, "F", 0),
             ("R", 6.73, -2.32, 0.6, "F", 0), ("+", 9.27, -2.32, 0.6, "F", 0),
             ("T", 6.73, 2.32, 0.6, "F", 0), ("G", 9.27, 2.32, 0.6, "F", 0)]
SILK_LINES = [((CUT_X, NECK_Y0), (CUT_X, NECK_Y1), "F")]
