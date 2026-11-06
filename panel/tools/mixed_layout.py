"""KiKit layout plugin: one panel carrying both v8.3 tags (D2 solar and D1 battery) for one JLCPCB order.

Layout (top view, every unit's far end towards a rail, tails towards the middle):

    | frame | D2 D2 D2 D2 D2 | bar | D1 D1 D1 D1 | frame |      top row: upright
    |       |   backbone across the panel (D1 side: teeth)   |
    | frame | D2 D2 D2 D2 D2 | bar | D1 D1 D1 D1 | frame |      bottom row: turned 180 deg

* Every unit keeps its own KiKit tab annotations (KT1 far end -> frame, KT2/KT3 sides -> neighbour or bar,
  KT4 tail end -> backbone). The default partition lines (mid-gap) already fall inside the bar and the backbone, so
  every tab ends in solid substrate.
* D1 is shorter than D2: a tooth on each side of the backbone under the D1 columns keeps its tail tabs 2 mm long.
* The backbone height is chosen so that the whole panel is >= 70 x 70 mm (JLCPCB Standard PCBA minimum).
* Nets are renamed "B{n}-{net}" so that later scripts can tell which unit (n) a footprint belongs to; the unit map
  (design and variant of every n) is written next to the panel as <panel>.units.json.

The plugin argument is the path of a JSON config (see tools/mixed_panel.json).
"""
import json
import os

from kikit.common import findBoardBoundingBox, fromDegrees, fromMm, toMm
from kikit.panelize import Origin, expandRect
from kikit.plugin import LayoutPlugin
from pcbnewTransition import pcbnew
from shapely.geometry import box


class MixedLayout(LayoutPlugin):
    def buildLayout(self, panel, inputFile, sourceArea):
        cfg_path = self.userArg
        with open(cfg_path) as f:
            cfg = json.load(f)
        base = os.path.dirname(os.path.abspath(cfg_path))
        hs, vs, bar_w = cfg["hspace"], cfg["vspace"], cfg["bar"]
        designs = {}
        for name, d in cfg["designs"].items():
            path = os.path.normpath(os.path.join(base, d["pcb"]))
            bb = findBoardBoundingBox(pcbnew.LoadBoard(path))
            designs[name] = dict(path=path, bb=bb, w=toMm(bb.GetWidth()), h=toMm(bb.GetHeight()))
        hmax = max(d["h"] for d in designs.values())

        # Columns: x extents
        cols, x = [], 0.0
        for c in cfg["columns"]:
            if c == "BAR":
                cols.append(dict(kind="bar", x0=x, x1=x + bar_w))
                x += bar_w + hs
            else:
                d = designs[c[0]]
                cols.append(dict(kind="unit", design=c[0], variant=c[1], x0=x, x1=x + d["w"]))
                x += d["w"] + hs
        x_end = x - hs
        # Height: top row, backbone, bottom row; backbone grown until the framed panel reaches the minimum size.
        frame = cfg["frame_width"] + cfg["frame_space"]
        bone = max(cfg["backbone_min"], cfg["min_panel"] - 2 * frame - 2 * hmax - 2 * vs)
        y_bone0, y_bone1 = hmax + vs, hmax + vs + bone
        y_end = y_bone1 + vs + hmax
        self.geometry = dict(width=x_end + 2 * frame, height=y_end + 2 * frame, backbone=bone, hmax=hmax)

        units, n = [], 0
        tol = fromMm(cfg["tolerance"])
        netpat = "B{n}-{orig}"
        for row in (0, 1):
            for c in cols:
                if c["kind"] != "unit":
                    continue
                d = designs[c["design"]]
                cx = (c["x0"] + c["x1"]) / 2
                cy = d["h"] / 2 if row == 0 else y_end - d["h"] / 2
                panel.appendBoard(d["path"], pcbnew.VECTOR2I(fromMm(cx), fromMm(cy)),
                                  sourceArea=expandRect(d["bb"], tol), origin=Origin.Center,
                                  rotationAngle=fromDegrees(0 if row == 0 else 180),
                                  netRenamer=lambda i, orig, n=n: netpat.format(n=i, orig=orig),
                                  refRenamer=lambda i, orig: orig, inheritDrc=(len(panel.substrates) == 0),
                                  interpretAnnotations=True)
                units.append(dict(n=len(panel.substrates) - 1, design=c["design"], variant=c["variant"],
                                  row=row + 1, col=cols.index(c) + 1))
                n += 1

        # Extra substrate: backbone (full width, into the frame), bars, teeth under the shorter design's columns.
        ov = 0.5
        pieces = [box(-frame + 0.01, y_bone0, x_end + frame - 0.01, y_bone1)]
        for c in cols:
            if c["kind"] == "bar":
                pieces.append(box(c["x0"], -vs - ov, c["x1"], y_bone0 + ov))
                pieces.append(box(c["x0"], y_bone1 - ov, c["x1"], y_end + vs + ov))
        # teeth: contiguous runs of columns of a design shorter than hmax
        run = []
        for c in cols + [dict(kind="end")]:
            short = c["kind"] == "unit" and designs[c["design"]]["h"] < hmax - 1e-6
            if short and (not run or run[-1]["design"] == c["design"]):
                run.append(c)
                continue
            if run:
                h = designs[run[0]["design"]]["h"]
                xa, xb = run[0]["x0"] - hs, run[-1]["x1"] + hs
                pieces.append(box(xa, h + vs, xb, y_bone0 + ov))
                pieces.append(box(xa, y_bone1 - ov, xb, y_end - h - vs))
                run = []
            if short:
                run = [c]
        for p in pieces:
            panel.appendSubstrate(box(*[fromMm(v) for v in p.bounds]))
        self.pieces = pieces

        out = cfg.get("units_out")
        if out:
            with open(os.path.join(base, out), "w") as f:
                json.dump(dict(units=units, geometry=self.geometry, netpattern="B{n}-"), f, indent=1)
        return panel.substrates
