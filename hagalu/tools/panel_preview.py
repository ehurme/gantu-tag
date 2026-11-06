"""Flat colour preview of the fab panel's top or bottom side (HASL pads, green mask, white silk, drills).
Usage (KiCad Python): python3.12 tools/panel_preview.py fab/<panel>.kicad_pcb docs/panel_top.png [top|bottom]
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import PathPatch  # noqa: E402
from matplotlib.path import Path  # noqa: E402
import pcbnew  # noqa: E402
from shapely.geometry import MultiPolygon, Point, Polygon  # noqa: E402
from shapely.ops import unary_union  # noqa: E402

COL = {"mask": "#1e5b34", "mask_cu": "#2f7d45", "fr4": "#b39b62", "hasl": "#cfd0cc", "silk": "#f2f2ee",
       "drill": "#16181a", "bg": "#1b1d20"}
src, out = sys.argv[1], sys.argv[2]
side = sys.argv[3] if len(sys.argv) > 3 else "top"
b = pcbnew.LoadBoard(src)
mm = pcbnew.ToMM


def polys(s):
    res = []
    for i in range(s.OutlineCount()):
        r = s.Outline(i)
        ext = [(mm(r.CPoint(j).x), mm(r.CPoint(j).y)) for j in range(r.PointCount())]
        holes = [[(mm(s.Hole(i, h).CPoint(j).x), mm(s.Hole(i, h).CPoint(j).y)) for j in range(s.Hole(i, h).PointCount())]
                 for h in range(s.HoleCount(i))]
        if len(ext) >= 3:
            res.append(Polygon(ext, holes).buffer(0))
    return unary_union(res) if res else MultiPolygon()


def layer(lid):
    s = pcbnew.SHAPE_POLY_SET()
    b.ConvertBrdLayerToPolygonalContours(lid, s)
    return polys(s)


ol = pcbnew.SHAPE_POLY_SET()
b.GetBoardPolygonOutlines(ol)
outline = polys(ol)
cu, mk, sk = ((pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_SilkS) if side == "top" else (pcbnew.B_Cu, pcbnew.B_Mask, pcbnew.B_SilkS))
cu, mk, sk = layer(cu).intersection(outline), layer(mk).intersection(outline), layer(sk).intersection(outline)
drills = [Point(mm(p.GetPosition().x), mm(p.GetPosition().y)).buffer(mm(p.GetDrillSize().x) / 2, 16)
          for fp in b.GetFootprints() for p in fp.Pads() if p.GetDrillSize().x > 0]
drills += [Point(mm(t.GetPosition().x), mm(t.GetPosition().y)).buffer(mm(t.GetDrillValue()) / 2, 12)
           for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
drill = unary_union(drills)
minx, miny, maxx, maxy = outline.bounds
W, H = maxx - minx, maxy - miny
px = 2400 / max(W, H)
fig = plt.figure(figsize=(W * px / 100 + 0.4, H * px / 100 + 0.4), dpi=100)
ax = fig.add_axes([0, 0, 1, 1])
pad = 0.2 * 100 / px
ax.set_xlim(minx - pad, maxx + pad)
ax.set_ylim(maxy + pad, miny - pad)
if side == "bottom":
    ax.invert_xaxis()
ax.axis("off")
fig.patch.set_facecolor(COL["bg"])


def draw(g, c):
    for p in ([g] if g.geom_type == "Polygon" else list(getattr(g, "geoms", []))):
        if p.is_empty or p.geom_type != "Polygon":
            continue
        v, k = [], []
        for ring in [p.exterior] + list(p.interiors):
            cc = list(ring.coords)
            v += cc
            k += [Path.MOVETO] + [Path.LINETO] * (len(cc) - 2) + [Path.CLOSEPOLY]
        ax.add_patch(PathPatch(Path(v, k), facecolor=c, edgecolor="none", lw=0))


draw(outline, COL["mask"])
draw(cu.difference(mk), COL["mask_cu"])
draw(mk.difference(cu), COL["fr4"])
draw(cu.intersection(mk), COL["hasl"])
draw(sk.difference(mk), COL["silk"])
draw(drill, COL["drill"])
fig.savefig(out, dpi=100, facecolor=COL["bg"])
print("wrote", out, f"({W:.1f} x {H:.1f} mm)")
