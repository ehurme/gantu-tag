"""Generate the project footprint library insect_tag.pretty (KiCad 7 format).

Footprints:
  InPlay_IN100_DFN-8-1EP_2.5x2.5mm_P0.5mm_EP1.3x1.9mm  IN100-D1-R-YC1I land pattern
  Crystal_SMD_1612-4Pin_1.6x1.2mm                       TXC 8Q26000008 (1.6 x 1.2 mm, 4 pads)
  Antenna_Arm_Feed                                      feed point of the printed antenna arm
  Cell_337_TopTabPads                                   two rim pads for the 337 cell's welded tabs
  ProgPads_2x02_P2.54mm_THT_Tab                         2 x 2 programming pads on the cut-off tab
  KiKit_Tab_*mm                                         KiKit panel tab annotations
"""
import os
import uuid

OUT = os.path.join(os.path.dirname(__file__), "..", "insect_tag.pretty")


def u():
    return str(uuid.uuid4())


def txt(kind, text, x, y, layer, size=0.5, thick=0.08, hide=False):
    h = " hide" if hide else ""
    return (f'  (fp_text {kind} "{text}" (at {x} {y}) (layer "{layer}"){h}\n'
            f'    (effects (font (size {size} {size}) (thickness {thick})))\n'
            f'    (tstamp {u()})\n  )\n')


def line(x1, y1, x2, y2, layer, w=0.1):
    return (f'  (fp_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type solid)) '
            f'(layer "{layer}") (tstamp {u()}))\n')


def rect(x1, y1, x2, y2, layer, w=0.05):
    return (line(x1, y1, x2, y1, layer, w) + line(x2, y1, x2, y2, layer, w) +
            line(x2, y2, x1, y2, layer, w) + line(x1, y2, x1, y1, layer, w))


def circle(cx, cy, r, layer, w=0.1):
    return (f'  (fp_circle (center {cx} {cy}) (end {cx + r} {cy}) (stroke (width {w}) (type solid)) '
            f'(fill none) (layer "{layer}") (tstamp {u()}))\n')


def smd(num, x, y, w, h, shape="roundrect", layers='"F.Cu" "F.Paste" "F.Mask"', extra=""):
    rr = " (roundrect_rratio 0.25)" if shape == "roundrect" else ""
    return (f'  (pad "{num}" smd {shape} (at {x} {y}) (size {w} {h}) (layers {layers}){rr}{extra} '
            f'(tstamp {u()}))\n')


def tht(num, x, y, d, drill, shape="circle"):
    return (f'  (pad "{num}" thru_hole {shape} (at {x} {y}) (size {d} {d}) (drill {drill}) '
            f'(layers "*.Cu" "*.Mask") (tstamp {u()}))\n')


def npth(x, y, d):
    return (f'  (pad "" np_thru_hole circle (at {x} {y}) (size {d} {d}) (drill {d}) '
            f'(layers "*.Cu" "*.Mask") (tstamp {u()}))\n')


def footprint(name, body, descr, tags, attr, layer="F.Cu"):
    return (f'(footprint "{name}" (version 20221018) (generator pcbnew)\n'
            f'  (layer "{layer}")\n  (descr "{descr}")\n  (tags "{tags}")\n'
            f'  (attr {attr})\n{body})\n')


def write(name, text):
    with open(os.path.join(OUT, name + ".kicad_mod"), "w") as f:
        f.write(text)


import math, sys
sys.path.insert(0, os.path.dirname(__file__))
import design as D


# --- IN100 DFN8 (YC1I: 2.5 x 2.5, e 0.5, b 0.2, L 0.3, exposed pad 1.3 x 1.9).
def in100(ep_h=1.9):
    name = f"InPlay_IN100_DFN-8-1EP_2.5x2.5mm_P0.5mm_EP1.3x{ep_h}mm"
    b = txt("reference", "REF**", 0, -1.9, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, 1.9, "F.Fab", 0.3, 0.05, hide=True)
    ys = [-0.75, -0.25, 0.25, 0.75]
    for i, y in enumerate(ys):
        b += smd(str(i + 1), -1.2, y, 0.65, 0.25)
    for i, y in enumerate(reversed(ys)):
        b += smd(str(i + 5), 1.2, y, 0.65, 0.25)
    b += smd("9", 0, 0, 1.3, ep_h, "rect", '"F.Cu" "F.Mask"')
    b += smd("", 0, 0, 0.9, min(1.2, ep_h - 0.5), "roundrect", '"F.Paste"')
    b += rect(-1.25, -1.25, 1.25, 1.25, "F.Fab", 0.08)
    b += line(-1.25, -0.75, -0.75, -1.25, "F.Fab", 0.08)
    b += rect(-1.6, -1.3, 1.6, 1.3, "F.CrtYd", 0.05)
    b += circle(-1.5, -1.1, 0.05, "F.SilkS", 0.1)
    write(name, footprint(name, b, f"InPlay IN100 DFN8 2.5x2.5 (IN100-D1-R-YC1I), EP 1.3x{ep_h}",
                          "IN100 NanoBeacon DFN8", "smd"))


# --- 1612 four-pad crystal (TXC 8Q / NDK NX1612SA class): pads 0.6 x 0.5 on a 1.05 x 0.75 grid.
#     Pin 1 bottom-left, 2 bottom-right, 3 top-right, 4 top-left (1/3 crystal, 2/4 lid ground).
def xtal1612():
    name = "Crystal_SMD_1612-4Pin_1.6x1.2mm"
    b = txt("reference", "REF**", 0, -1.1, "F.Fab", 0.4, 0.06)
    b += txt("value", name, 0, 1.1, "F.Fab", 0.3, 0.05, hide=True)
    for num, x, y in [("1", -0.525, 0.375), ("2", 0.525, 0.375), ("3", 0.525, -0.375), ("4", -0.525, -0.375)]:
        b += smd(num, x, y, 0.6, 0.5, "rect")
    b += rect(-0.8, -0.6, 0.8, 0.6, "F.Fab", 0.08)
    b += rect(-0.95, -0.75, 0.95, 0.75, "F.CrtYd", 0.05)
    write(name, footprint(name, b, "1.6 x 1.2 mm four-pad crystal; land pattern from the NDK NX1612SA terminal grid",
                          "crystal 1612", "smd"))


# --- antenna feed point at the root of the arm (the trace up the arm is a track on the RF net)
def ant_feed():
    """Feed point plus end point of the printed antenna. Both pads are number 1, so the antenna track up the arm
    connects pad to pad (no dangling-track warning)."""
    name = "Antenna_Arm_Feed"
    feed = next(p for p in D.PARTS if p["ref"] == "AE1")["pcb"]
    tip = round(D.ARM_TIP_Y + 0.5 - feed[1], 4)        # arm-tip end of the trace, relative to the feed
    b = txt("reference", "REF**", 0, tip / 2, "F.Fab", 0.4, 0.06)
    b += txt("value", "ANT", 0.6, 0.5, "F.Fab", 0.3, 0.05, hide=True)
    b += smd("1", 0, 0, 0.2, 0.2, "rect", '"F.Cu"')
    b += smd("1", 0, tip, 0.2, 0.2, "rect", '"F.Cu"')
    b += line(0, 0, 0, tip, "F.Fab", 0.25)
    write(name, footprint(name, b, "Printed quarter-wave antenna on the arm: feed and end points", "antenna",
                          "smd exclude_from_pos_files exclude_from_bom allow_missing_courtyard"))


# --- battery ear pads (origin = tag centre): round pads centred on the two outline ears
def cell_ears():
    name = "Cell_337_TopTabPads"
    b = txt("reference", "REF**", 0, 3.3, "F.Fab", 0.4, 0.06)
    b += txt("value", "337", 0, 3.8, "F.Fab", 0.3, 0.05, hide=True)
    for num in ("1", "2"):
        x, y = D.BT_PADS[num]
        b += smd(num, round(x, 4), round(y, 4), D.BT_PAD_D, D.BT_PAD_D, "circle", '"F.Cu" "F.Mask"')
        b += txt("user", "+" if num == "1" else "-", round(x, 3), round(y - 0.6, 3), "F.Fab", 0.4, 0.06)
    b += circle(0, 0, 2.4, "F.Fab", 0.05)
    write(name, footprint(name, b, "Top-side pads at the rim for a 337 (SR416SW) cell's welded tabs. Cell sits under the tag on Kapton.",
                          "battery 337 tab", "smd exclude_from_pos_files exclude_from_bom allow_missing_courtyard"))



def prog2x2():
    name = "ProgPads_2x02_P2.54mm_THT_Tab"
    # Origin = centre of the 2 x 2 grid. 3 RXD top-left, 4 VCC top-right, 2 TXD bottom-left, 1 GND bottom-right.
    b = txt("reference", "REF**", 0, -3.2, "F.Fab", 0.5, 0.08)
    b += txt("value", name, 0, 3.2, "F.Fab", 0.3, 0.05, hide=True)
    b += tht("3", -1.27, -1.27, 1.4, 0.7)
    b += tht("4", 1.27, -1.27, 1.4, 0.7)
    b += tht("2", -1.27, 1.27, 1.4, 0.7)
    b += tht("1", 1.27, 1.27, 1.4, 0.7, "rect")
    b += rect(-2.17, -2.17, 2.17, 2.17, "F.CrtYd", 0.05)
    write(name, footprint(name, b, "Programming pads on the cut-off tab, 2 x 2 at 2.54 mm: RXD VCC / TXD GND",
                          "programming pogo pads", "through_hole exclude_from_pos_files exclude_from_bom"))

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
    in100(1.9); xtal1612(); ant_feed(); cell_ears(); prog2x2()
    for w in (0.6, 1.0, 1.2):
        kikit_tab(w)
    print(sorted(os.listdir(OUT)))
