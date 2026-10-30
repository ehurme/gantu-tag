"""Run KiCad DRC on the board, verify schematic/board net parity, and render PNG previews.

Usage: /usr/bin/python3 tools/check.py [outdir]
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D  # noqa: E402
from build import parse  # noqa: E402

PRJ = os.path.abspath(os.path.join(HERE, ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PRJ, "docs")
os.makedirs(OUT, exist_ok=True)


def drc():
    import pcbnew
    board = pcbnew.LoadBoard(os.path.join(PRJ, D.PROJECT + ".kicad_pcb"))
    rpt = os.path.join(OUT, "drc_report.txt")
    pcbnew.WriteDRCReport(board, rpt, pcbnew.EDA_UNITS_MILLIMETRES, True)
    txt = open(rpt).read()
    viol = re.findall(r"^\[(\w+)\]: (.*)$", txt, re.M)
    summary = {k: int(v) for k, v in re.findall(r"\*\* Found (\d+) (\w[\w ]*?) \*\*", txt) and
               [(m[1], m[0]) for m in re.findall(r"\*\* Found (\d+) ([\w ]+?) \*\*", txt)]}
    return txt, viol, summary, board


def parity(board):
    """Compare pad nets on the board with the design netlist (what the schematic was built from)."""
    want = {}
    for net, pins in D.NETS.items():
        for r, p in pins:
            want[(r, p)] = net if net in D.POWER_NETS else "/" + net
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


def render():
    pcb = os.path.join(PRJ, D.PROJECT + ".kicad_pcb")
    outs = []
    for name, layers, mirror in [
        ("pcb_top", "F.Cu,F.Paste,F.SilkS,F.Mask,Edge.Cuts,F.Fab", False),
        ("pcb_bottom", "B.Cu,B.SilkS,B.Mask,Edge.Cuts,B.Fab", True),
        ("pcb_copper_both", "F.Cu,B.Cu,Edge.Cuts", False),
    ]:
        svg = os.path.join(OUT, name + ".svg")
        cmd = ["kicad-cli", "pcb", "export", "svg", "--layers", layers, "--exclude-drawing-sheet",
               "--page-size-mode", "2", "-o", svg, pcb]
        if mirror:
            cmd.insert(4, "--mirror")
        subprocess.run(cmd, check=True, capture_output=True)
        outs.append(svg)
    return outs


if __name__ == "__main__":
    txt, viol, summary, board = drc()
    print("DRC summary:", re.findall(r"\*\* Found \d+ [\w ]+ \*\*", txt))
    for kind, msg in viol:
        print(f"  [{kind}] {msg}")
    bad = parity(board)
    print("board/design net parity:", "OK" if not bad else bad)
    print("renders:", render())
