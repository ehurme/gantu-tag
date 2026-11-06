"""KiCad 7 checks for a board or panel: DRC (pcbnew.WriteDRCReport), board-versus-design net parity, pour islands,
and (for D1) copper inside the cell's crimp keep-out ring.

Usage: python3.12 tools/check.py [board.kicad_pcb] [report dir]
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D  # noqa: E402
import pcbnew  # noqa: E402

PRJ = os.path.abspath(os.path.join(HERE, ".."))
BOARD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PRJ, D.PROJECT + ".kicad_pcb")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PRJ, "docs")
os.makedirs(OUT, exist_ok=True)
mm = pcbnew.ToMM


def drc(board, name):
    rpt = os.path.join(OUT, name)
    pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(rpt).read()
    counts = {m[1]: int(m[0]) for m in re.findall(r"\*\* Found (\d+) ([\w ]+?) \*\*", txt)}
    items = re.findall(r"^\[(\w+)\]: (.*)\n(.*)\n\s*(@.*)\n(?:\s*(@.*)\n)?", txt, re.M)
    return counts, items, txt


def parity(board):
    want = {}
    for net, pins in D.NETS.items():
        for r, p in pins:
            want[(r, p)] = net if net in D.POWER_SYMBOLS else "/" + net
    bad = []
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        for pad in fp.Pads():
            num = pad.GetNumber()
            if not num:
                continue
            got = pad.GetNetname()
            exp = want.get((ref, num))
            if exp is None and got and not got.startswith("unconnected-"):
                bad.append(f"{ref}.{num} has net {got} but design has none")
            elif exp is not None and got != exp:
                bad.append(f"{ref}.{num} net {got!r} != design {exp!r}")
    return bad


def islands(board):
    """Each filled pour polygon must touch at least one item of its own net that is not itself a pour."""
    from shapely.geometry import Polygon, Point
    report = []
    items = {}
    for t in board.GetTracks():
        layers = ("F", "B") if t.GetClass() == "PCB_VIA" else (("F",) if t.GetLayer() == pcbnew.F_Cu else ("B",))
        for L in layers:
            items.setdefault((t.GetNetname(), L), []).append(Point(mm(t.GetStart().x), mm(t.GetStart().y)))
            items.setdefault((t.GetNetname(), L), []).append(Point(mm(t.GetEnd().x), mm(t.GetEnd().y)))
    for fp in board.GetFootprints():
        for p in fp.Pads():
            for L, lid in (("F", pcbnew.F_Cu), ("B", pcbnew.B_Cu)):
                if p.IsOnLayer(lid):
                    items.setdefault((p.GetNetname(), L), []).append(Point(mm(p.GetPosition().x), mm(p.GetPosition().y)))
    for z in board.Zones():
        if z.GetIsRuleArea():
            continue
        for lid, L in ((pcbnew.F_Cu, "F"), (pcbnew.B_Cu, "B")):
            if not z.IsOnLayer(lid):
                continue
            ps = z.GetFilledPolysList(lid)
            for i in range(ps.OutlineCount()):
                ol = ps.Outline(i)
                poly = Polygon([(mm(ol.CPoint(j).x), mm(ol.CPoint(j).y)) for j in range(ol.PointCount())]).buffer(0.05)
                hit = any(poly.contains(pt) for pt in items.get((z.GetNetname(), L), []))
                if not hit:
                    c = poly.centroid
                    report.append(f"{z.GetNetname()} pour island on {L}.Cu near ({c.x - 100:.2f}, {c.y - 100:.2f}), "
                                  f"area {poly.area:.3f} mm2")
    return report


def keepout_ring(board, origin=(100.0, 100.0)):
    """D1 only: exposed copper (pads, via holes) or non-VCC vias on the bottom inside the crimp ring."""
    ring = getattr(D, "KEEPOUT_RING", None)
    if not ring:
        return []
    r0, r1 = ring
    out = []
    ox, oy = origin

    def rr(x, y):
        return math.hypot(mm(x) - ox, mm(y) - oy)
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            r = rr(t.GetPosition().x, t.GetPosition().y)
            if r0 - 0.25 < r < r1 + 0.25 and t.GetNetname() != "VCC":
                out.append(f"tented {t.GetNetname()} via at r = {r:.2f} mm "
                           f"({mm(t.GetPosition().x) - ox:.2f}, {mm(t.GetPosition().y) - oy:.2f})")
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnLayer(pcbnew.B_Cu) or not p.IsOnLayer(pcbnew.B_Mask):
                continue
            r = rr(p.GetPosition().x, p.GetPosition().y)
            ext = max(mm(p.GetSize().x), mm(p.GetSize().y)) / 2
            if r - ext < r1 and r + ext > r0 and p.GetNetname() != "VCC":
                out.append(f"EXPOSED {p.GetNetname()} pad {fp.GetReference()}.{p.GetNumber()} at r = {r:.2f} mm")
    return out


if __name__ == "__main__":
    board = pcbnew.LoadBoard(BOARD)
    name = "drc_report.txt" if BOARD.endswith(D.PROJECT + ".kicad_pcb") else os.path.basename(BOARD).replace(".kicad_pcb", "_drc.txt")
    counts, items, txt = drc(board, name)
    print("DRC:", counts)
    for kind, msg, rule, a, b in items[:60]:
        print(f"  [{kind}] {msg} | {rule.strip()} | {a.strip()} | {(b or '').strip()}")
    if BOARD.endswith(D.PROJECT + ".kicad_pcb"):
        bad = parity(board)
        print("board/design net parity:", "OK" if not bad else bad)
    isl = islands(board)
    print("pour islands:", "none" if not isl else isl)
    if not BOARD.endswith("panel.kicad_pcb") and "panel" not in os.path.basename(BOARD):
        ko = keepout_ring(board)
        print("crimp keep-out ring:", "clean" if not ko else ko)
