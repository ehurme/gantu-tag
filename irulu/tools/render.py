"""Render a colour preview of the tag (top, both copper layers, bottom) to docs/pcb_preview.png.

Usage: HOME=/root /usr/bin/python3 tools/render.py [out.png]
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Circle, Polygon as MPoly  # noqa: E402
import pcbnew  # noqa: E402
import shapely.affinity  # noqa: E402
from shapely.geometry import box  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D  # noqa: E402

PRJ = os.path.abspath(os.path.join(HERE, ".."))
X0 = Y0 = 100.0
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PRJ, "docs", "pcb_preview.png")

COL = {"F": "#c8783c", "B": "#3c78c8", "board": "#1d5c3a", "edge": "#e8e8e8", "silk": "#f4f4f4",
       "via": "#d8d8d8", "hole": "#101010", "bg": "#121417"}


def mm(v):
    return pcbnew.ToMM(v)


def load():
    b = pcbnew.LoadBoard(os.path.join(PRJ, D.PROJECT + ".kicad_pcb"))
    data = {"pads": [], "tracks": [], "vias": [], "zones": [], "text": [], "lines": []}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            cx, cy = mm(p.GetPosition().x) - X0, mm(p.GetPosition().y) - Y0
            sx, sy = mm(p.GetSize().x), mm(p.GetSize().y)
            if p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE:
                g = ("circle", cx, cy, sx / 2)
            else:
                r = box(-sx / 2, -sy / 2, sx / 2, sy / 2)
                r = shapely.affinity.rotate(r, -p.GetOrientationDegrees(), origin=(0, 0))
                g = ("poly", list(shapely.affinity.translate(r, cx, cy).exterior.coords))
            layers = [L for L, lid in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu)) if p.IsOnLayer(lid)]
            drill = mm(p.GetDrillSize().x) if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else 0
            data["pads"].append((g, layers, (drill, cx, cy)))
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA":
            data["vias"].append((mm(t.GetPosition().x) - X0, mm(t.GetPosition().y) - Y0,
                                 mm(t.GetWidth()) / 2, mm(t.GetDrillValue()) / 2))
        else:
            L = "F" if t.GetLayer() == pcbnew.F_Cu else "B"
            data["tracks"].append((L, mm(t.GetStart().x) - X0, mm(t.GetStart().y) - Y0,
                                   mm(t.GetEnd().x) - X0, mm(t.GetEnd().y) - Y0, mm(t.GetWidth())))
    for z in b.Zones():
        for lid, L in ((pcbnew.F_Cu, "F"), (pcbnew.B_Cu, "B")):
            if not z.IsOnLayer(lid):
                continue
            ps = z.GetFilledPolysList(lid)
            for i in range(ps.OutlineCount()):
                ol = ps.Outline(i)
                pts = [(mm(ol.CPoint(j).x) - X0, mm(ol.CPoint(j).y) - Y0) for j in range(ol.PointCount())]
                holes = []
                for h in range(ps.HoleCount(i)):
                    hc = ps.Hole(i, h)
                    holes.append([(mm(hc.CPoint(j).x) - X0, mm(hc.CPoint(j).y) - Y0) for j in range(hc.PointCount())])
                data["zones"].append((L, pts, holes))
    for d in b.GetDrawings():
        if d.GetClass() in ("PCB_TEXT",):
            L = "F" if d.GetLayer() == pcbnew.F_SilkS else "B"
            data["text"].append((L, d.GetText(), mm(d.GetPosition().x) - X0, mm(d.GetPosition().y) - Y0,
                                 mm(d.GetTextHeight())))
        elif d.GetClass() == "PCB_SHAPE" and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            L = "F" if d.GetLayer() == pcbnew.F_SilkS else "B"
            data["lines"].append((L, mm(d.GetStart().x) - X0, mm(d.GetStart().y) - Y0,
                                  mm(d.GetEnd().x) - X0, mm(d.GetEnd().y) - Y0))
    return data


def draw(ax, data, layers, silk_side, title, xlim, ylim, mirror=False):
    from shapely.geometry import Polygon
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    outline = D.outline_polygon()
    ax.set_facecolor(COL["bg"])
    ax.add_patch(MPoly(list(outline.exterior.coords), closed=True, fc=COL["board"], ec=COL["edge"], lw=0.8, zorder=1))
    for L in layers:
        a = 0.9 if len(layers) == 1 else 0.6
        for zl, pts, holes in data["zones"]:
            if zl != L:
                continue
            verts, codes = [], []
            for ring in [pts] + holes:
                verts += ring + [ring[0]]
                codes += [Path.MOVETO] + [Path.LINETO] * (len(ring) - 1) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), fc=COL[L], ec="none", alpha=a * 0.75, zorder=2))
        for tl, x1, y1, x2, y2, w in data["tracks"]:
            if tl == L:
                ax.plot([x1, x2], [y1, y2], color=COL[L], lw=w * PT, solid_capstyle="round", alpha=a, zorder=3)
        for g, pl, drill in data["pads"]:
            if L not in pl:
                continue
            if g[0] == "circle":
                ax.add_patch(Circle((g[1], g[2]), g[3], fc=COL[L], ec="none", alpha=a + 0.1 if a < 0.9 else 1, zorder=4))
            else:
                ax.add_patch(MPoly(g[1], closed=True, fc=COL[L], ec="none", alpha=a + 0.1 if a < 0.9 else 1, zorder=4))
    for x, y, r, dr in data["vias"]:
        ax.add_patch(Circle((x, y), r, fc=COL["via"], ec="none", zorder=5))
        ax.add_patch(Circle((x, y), dr, fc=COL["hole"], ec="none", zorder=6))
    for g, pl, (drill, cx, cy) in data["pads"]:
        if drill:
            ax.add_patch(Circle((cx, cy), drill / 2, fc=COL["hole"], ec="none", zorder=6))
    if silk_side:
        for L, txt, x, y, h in data["text"]:
            if L == silk_side:
                ax.text(x, y, txt, color=COL["silk"], fontsize=h * PT * 1.25, ha="center", va="center",
                        fontweight="bold", zorder=7, transform=ax.transData)
        for L, x1, y1, x2, y2 in data["lines"]:
            if L == silk_side:
                ax.plot([x1, x2], [y1, y2], color=COL["silk"], lw=0.12 * PT, zorder=7)
    ax.set_xlim(*(xlim[::-1] if mirror else xlim))
    ax.set_ylim(ylim[1], ylim[0])
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, color="#dddddd", fontsize=11)


if __name__ == "__main__":
    data = load()
    xlim, ylim = (-4.0, 4.0), (-4.0, 12.6)
    fig, axes = plt.subplots(1, 3, figsize=(15, 9.6), facecolor=COL["bg"])
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.01, wspace=0.04)
    PT = (axes[0].get_position().width * 15 * 72) / (xlim[1] - xlim[0])
    draw(axes[0], data, ["F"], "F", "Top (parts side)", xlim, ylim)
    draw(axes[1], data, ["B", "F"], None, "Both copper layers (orange top, blue bottom)", xlim, ylim)
    draw(axes[2], data, ["B"], "B", "Bottom (mirrored, against the cell)", xlim, ylim, mirror=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=110, facecolor=COL["bg"])
    print(OUT)
