"""3D renders of the board, top and bottom, to docs/pcb_3d_top.png and docs/pcb_3d_bottom.png.

Two stages, because KiCad 7's pcbnew and the VTK renderer live in different Pythons on the build container:
  1. (KiCad Python) rasterise the copper / mask / silk layers of each side into textures (lead-free HASL pads,
     green mask, white silk, dark drills) and list the footprints' 3D models with their placement;
  2. (Python with pyvista, under xvfb-run) extrude the outline, texture both faces, add the parts' VRML models and
     render an oblique view of each side.
Usage (from the project folder):  python3.12 tools/render3d.py   (runs stage 2 itself with RENDER_PY, default python3)
The button-cell and antenna-wire models are left out so the cell rings, pads and antenna holes stay visible.
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PRJ = os.path.abspath(os.path.join(HERE, ".."))
TMP = os.path.join(PRJ, "docs", ".render3d")
PXMM = 60
SKIP_MODELS = ("Cell_Button", "Antenna_WirePad", "BatteryPads")
COL = {"mask": "#1e5b34", "mask_cu": "#2f7d45", "fr4": "#b39b62", "hasl": "#cfd0cc", "silk": "#f2f2ee",
       "drill": "#16181a"}


def stage1():
    sys.path.insert(0, HERE)
    import design as D
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.path import Path
    from matplotlib.patches import PathPatch
    import pcbnew
    from shapely.geometry import Polygon, MultiPolygon, Point
    from shapely.ops import unary_union

    X0 = Y0 = 100.0
    mm = pcbnew.ToMM
    b = pcbnew.LoadBoard(os.path.join(PRJ, D.PROJECT + ".kicad_pcb"))
    outline = D.outline_polygon().simplify(0.002)
    minx, miny, maxx, maxy = outline.bounds
    t = D.BOARD_THICKNESS

    def layer_geom(lid):
        s = pcbnew.SHAPE_POLY_SET()
        b.ConvertBrdLayerToPolygonalContours(lid, s)
        polys = []
        for i in range(s.OutlineCount()):
            ring = s.Outline(i)
            ext = [(mm(ring.CPoint(j).x) - X0, mm(ring.CPoint(j).y) - Y0) for j in range(ring.PointCount())]
            holes = []
            for h in range(s.HoleCount(i)):
                hr = s.Hole(i, h)
                holes.append([(mm(hr.CPoint(j).x) - X0, mm(hr.CPoint(j).y) - Y0) for j in range(hr.PointCount())])
            if len(ext) >= 3:
                p = Polygon(ext, holes).buffer(0)
                if not p.is_empty:
                    polys.append(p)
        return unary_union(polys) if polys else MultiPolygon()

    drills = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.GetDrillSize().x > 0:
                drills.append(Point(mm(p.GetPosition().x) - X0, mm(p.GetPosition().y) - Y0).buffer(mm(p.GetDrillSize().x) / 2, 24))
    for tr in b.GetTracks():
        if tr.GetClass() == "PCB_VIA":
            drills.append(Point(mm(tr.GetPosition().x) - X0, mm(tr.GetPosition().y) - Y0).buffer(mm(tr.GetDrillValue()) / 2, 16))
    drill = unary_union(drills) if drills else MultiPolygon()

    W, H = maxx - minx, maxy - miny
    os.makedirs(TMP, exist_ok=True)

    def draw(geom, ax, color):
        geoms = [geom] if geom.geom_type == "Polygon" else list(getattr(geom, "geoms", []))
        for g in geoms:
            if g.is_empty or g.geom_type != "Polygon":
                continue
            verts, codes = [], []
            for ring in [g.exterior] + list(g.interiors):
                c = list(ring.coords)
                verts += c
                codes += [Path.MOVETO] + [Path.LINETO] * (len(c) - 2) + [Path.CLOSEPOLY]
            ax.add_patch(PathPatch(Path(verts, codes), facecolor=color, edgecolor="none", lw=0, antialiased=True))

    for side, cu, mk, sk in (("top", pcbnew.F_Cu, pcbnew.F_Mask, pcbnew.F_SilkS),
                             ("bottom", pcbnew.B_Cu, pcbnew.B_Mask, pcbnew.B_SilkS)):
        cu_g = layer_geom(cu).intersection(outline)
        mk_g = layer_geom(mk).intersection(outline)
        sk_g = layer_geom(sk).intersection(outline)
        fig = plt.figure(figsize=(W * PXMM / 100, H * PXMM / 100), dpi=100)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(minx, maxx)
        ax.set_ylim(maxy, miny)          # board y points down; the image's top row is the board's min y
        ax.axis("off")
        fig.patch.set_alpha(0)
        draw(outline, ax, COL["mask"])
        draw(cu_g.difference(mk_g), ax, COL["mask_cu"])
        draw(mk_g.difference(cu_g), ax, COL["fr4"])
        draw(cu_g.intersection(mk_g), ax, COL["hasl"])
        draw(sk_g.difference(mk_g), ax, COL["silk"])
        draw(drill, ax, COL["drill"])
        path = os.path.join(TMP, f"tex_{side}.png")
        fig.savefig(path, dpi=100, transparent=True)
        plt.close(fig)
        from PIL import Image                # opaque RGB: an alpha channel makes VTK draw the face see-through
        im = Image.open(path).convert("RGBA")
        bg = Image.new("RGBA", im.size, COL["mask"])
        Image.alpha_composite(bg, im).convert("RGB").save(path)

    models = []
    for fp in b.GetFootprints():
        if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES:     # not fitted (DNP) or not a placed part
            continue
        for m in fp.Models():
            name = os.path.basename(m.m_Filename)
            if any(name.startswith(s) for s in SKIP_MODELS):
                continue
            path = os.path.join(PRJ, "insect_tag.3dshapes", name)
            if os.path.exists(path):
                models.append(dict(path=path, x=mm(fp.GetPosition().x) - X0, y=mm(fp.GetPosition().y) - Y0,
                                   rot=fp.GetOrientationDegrees(), flipped=fp.IsFlipped(),
                                   dz=m.m_Offset.z))
    json.dump(dict(outline=list(outline.exterior.coords), bounds=[minx, miny, maxx, maxy], thickness=t,
                   models=models, project=D.PROJECT), open(os.path.join(TMP, "scene.json"), "w"))


def parse_wrl(path):
    txt = open(path).read()
    shapes = []
    for m in re.finditer(r"diffuseColor ([\d.]+) ([\d.]+) ([\d.]+).*?point \[(.*?)\].*?coordIndex \[(.*?)\]", txt, re.S):
        col = tuple(float(m.group(i)) for i in (1, 2, 3))
        pts = [tuple(float(v) * 2.54 for v in p.split()) for p in m.group(4).split(",") if p.strip()]
        idx = [int(v) for v in m.group(5).replace(",", " ").split()]
        faces, cur = [], []
        for i in idx:
            if i == -1:
                if len(cur) >= 3:
                    faces.append(cur)
                cur = []
            else:
                cur.append(i)
        shapes.append((col, pts, faces))
    return shapes


def stage2():
    import math
    import numpy as np
    import pyvista as pv
    sc = json.load(open(os.path.join(TMP, "scene.json")))
    minx, miny, maxx, maxy = sc["bounds"]
    t = sc["thickness"]
    ring = sc["outline"][:-1]
    W, H = maxx - minx, maxy - miny

    def cap(z, tex):
        pts = np.array([(x, -y, z) for x, y in ring])
        face = np.hstack([[len(pts)], np.arange(len(pts))])
        m = pv.PolyData(pts, face).triangulate()
        u = (m.points[:, 0] - minx) / W
        v = (m.points[:, 1] + maxy) / H        # world y = -board y; image row 0 = board min y = world max y
        m.active_texture_coordinates = np.c_[u, v]
        return m, pv.read_texture(tex)

    pl = pv.Plotter(off_screen=True, window_size=(1600, 1600))
    pl.set_background("#1b1d20")
    top, ttop = cap(0.0, os.path.join(TMP, "tex_top.png"))
    bot, tbot = cap(-t, os.path.join(TMP, "tex_bottom.png"))
    pl.add_mesh(top, texture=ttop, ambient=0.35, diffuse=0.7, specular=0.15)
    pl.add_mesh(bot, texture=tbot, ambient=0.35, diffuse=0.7, specular=0.15)
    wall_pts = np.array([(x, -y, 0.0) for x, y in ring])
    wall = pv.PolyData(wall_pts, np.hstack([[len(wall_pts)], np.arange(len(wall_pts))])).extrude((0, 0, -t), capping=False)
    pl.add_mesh(wall, color="#c8b27a", ambient=0.3)
    cache = {}
    for md in sc["models"]:
        if md["path"] not in cache:
            cache[md["path"]] = parse_wrl(md["path"])
        a = math.radians(md["rot"])
        ca, sa = math.cos(a), math.sin(a)
        for col, pts, faces in cache[md["path"]]:
            P = []
            for x, y, z in pts:               # VRML: x right, y up, z up (KiCad model convention)
                if md["flipped"]:
                    x, z = -x, -z - t
                X = md["x"] + x * ca - y * sa
                Y = -md["y"] + x * sa + y * ca
                P.append((X, Y, z + md["dz"]))
            fl = np.hstack([[len(f)] + f for f in faces])
            pl.add_mesh(pv.PolyData(np.array(P), fl), color=col, ambient=0.3, diffuse=0.75, specular=0.3,
                        smooth_shading=False)
    cx, cy = (minx + maxx) / 2, -(miny + maxy) / 2
    D_ = max(W, H) * 2.3
    out_dir = os.path.join(PRJ, "docs")
    for side, zs in (("top", 1), ("bottom", -1)):
        pl.camera.focal_point = (cx, cy, -t / 2)
        pl.camera.position = (cx + 0.2 * D_, cy - 0.45 * D_, zs * 1.0 * D_)
        pl.camera.up = (0, 1, 0)
        pl.camera.view_angle = 22
        pl.reset_camera_clipping_range()
        pl.render()
        pl.screenshot(os.path.join(out_dir, f"pcb_3d_{side}.png"))
    pl.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "stage2":
        stage2()
    else:
        stage1()
        env = dict(os.environ)
        cmd = ["xvfb-run", "-a", os.environ.get("RENDER_PY", "python3"), os.path.abspath(__file__), "stage2"]
        subprocess.run(cmd, check=True, cwd=PRJ, env=env)
        print("wrote docs/pcb_3d_top.png and docs/pcb_3d_bottom.png")
