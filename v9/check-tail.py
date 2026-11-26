#!/usr/bin/env python3
"""Verify that body nets stay connected after removing the programming tail."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import pcbnew


PROJECTS = (
    ("hagalu/hagalu_v9_s6", 103.58, {"J1", "TP1", "TP2"}),
    ("irulu-337/irulu_v9_337", 103.210767, {"J1", "JP1"}),
)


def check_tail(source, cut_y, tail_references, kicad, work):
    board = pcbnew.LoadBoard(str(source))
    cut = pcbnew.FromMM(cut_y)
    footprints = list(board.GetFootprints())
    removed = {fp.GetReference() for fp in footprints if fp.GetPosition().y >= cut}
    if removed != tail_references:
        sys.exit(f"{source.stem} cut at Y={cut_y} mm removes {sorted(removed)}")

    for footprint in footprints:
        if footprint.GetReference() in tail_references:
            board.Remove(footprint)

    tracks = list(board.GetTracks())
    for track in tracks:
        if isinstance(track, pcbnew.PCB_VIA):
            if track.GetPosition().y >= cut:
                board.Remove(track)
            continue
        if isinstance(track, pcbnew.PCB_ARC):
            sys.exit(f"{source.stem} uses arc tracks. Extend the cut check before use.")

        start, end = track.GetStart(), track.GetEnd()
        if start.y >= cut and end.y >= cut:
            board.Remove(track)
        elif start.y >= cut or end.y >= cut:
            x = start.x + (end.x - start.x) * (cut - start.y) / (end.y - start.y)
            intersection = pcbnew.VECTOR2I(round(x), cut)
            if start.y >= cut:
                track.SetStart(intersection)
            else:
                track.SetEnd(intersection)

    work.mkdir()
    candidate = work / source.name
    if not pcbnew.SaveBoard(str(candidate), board):
        sys.exit(f"Could not save temporary board for {source.stem}")
    shutil.copyfile(source.with_suffix(".kicad_pro"), candidate.with_suffix(".kicad_pro"))
    report = work / "drc.json"
    subprocess.run(
        [kicad, "pcb", "drc", "--format", "json", "-o", str(report), str(candidate)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    openings = json.loads(report.read_text())["unconnected_items"]
    print(f"{source.stem} at Y={cut_y} mm: {len(openings)} open connections")
    for issue in openings:
        print("  " + " / ".join(item["description"] for item in issue["items"]))
    return not openings


def main():
    v9 = Path(__file__).resolve().parent
    kicad = (
        os.environ.get("KICAD_CLI")
        or shutil.which("kicad-cli")
        or "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
    )
    projects = {Path(project).stem: (project, cut_y, refs) for project, cut_y, refs in PROJECTS}
    if len(sys.argv) == 1:
        # KiCad's Python bindings need a fresh process for each modified board.
        results = [
            subprocess.run([sys.executable, __file__, name]).returncode for name in projects
        ]
        return int(any(results))
    if len(sys.argv) != 2 or sys.argv[1] not in projects:
        sys.exit(f"Usage: {Path(__file__).name} [{' | '.join(projects)}]")
    project, cut_y, refs = projects[sys.argv[1]]
    source = (v9 / project).with_suffix(".kicad_pcb")
    with tempfile.TemporaryDirectory(prefix="gantu-v9-tail-") as work:
        return int(not check_tail(source, cut_y, refs, kicad, Path(work) / source.stem))


if __name__ == "__main__":
    sys.exit(main())
