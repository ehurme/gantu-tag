"""Build the KiCad project (schematic, symbol lib, board, project rules) from design.py.

Derived from v7's build.py and made generic for the three v8 designs:
  - custom symbols come from design.SYMBOLS (IN100, supervisor, MOSFET pair, sensors, XIAO, ...)
  - pours and rule areas come from design.ZONES / design.KEEPOUTS
  - vias may carry their own size
  - zones are refilled after the project's design rules exist (refill(), as in v7)

Run with KiCad 7's Python:  python3.12 tools/build.py
"""
import json
import math
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D  # noqa: E402

PRJ = os.path.abspath(os.path.join(HERE, ".."))
LIB = getattr(D, "LIB", "insect_tag")
SYMDIR = "/usr/share/kicad/symbols"
FPDIR = "/usr/share/kicad/footprints"
G = 1.27  # schematic grid


def U():
    return str(uuid.uuid4())


# ============================================================ S-expressions (as v7)
class Q(str):
    """A quoted string token."""


def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in " \t\r\n":
            i += 1
        elif c in "()":
            yield c
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while s[j] != '"':
                if s[j] == "\\":
                    buf.append(s[j:j + 2])
                    j += 2
                else:
                    buf.append(s[j])
                    j += 1
            yield Q("".join(buf))
            i = j + 1
        else:
            j = i
            while j < n and s[j] not in ' \t\r\n()"':
                j += 1
            yield s[i:j]
            i = j


def parse(s):
    stack = [[]]
    for t in tokenize(s):
        if t == "(":
            stack.append([])
        elif t == ")":
            x = stack.pop()
            stack[-1].append(x)
        else:
            stack[-1].append(t)
    return stack[0][0]


def dump(x, ind=0):
    if isinstance(x, list):
        if not any(isinstance(e, list) for e in x):
            return "(" + " ".join(dump(e) for e in x) + ")"
        head, rest = [], []
        for e in x:
            (rest if (isinstance(e, list) or rest) else head).append(e)
        s = "(" + " ".join(dump(e) for e in head)
        for e in rest:
            s += "\n" + "  " * (ind + 1) + dump(e, ind + 1)
        return s + ")"
    if isinstance(x, Q):
        return '"' + x + '"'
    return str(x)


# ============================================================ custom symbols
PIN_TYPES = {"in": "input", "out": "output", "bidi": "bidirectional", "pwr": "power_in", "pout": "power_out",
             "pas": "passive", "nc": "no_connect", "oc": "open_collector"}


def make_symbol(name, spec):
    """spec: dict(value, footprint, descr, keywords, pins=[(num, name, side L/R/T/B, type key)], width)."""
    pins = spec["pins"]
    sides = {s: [p for p in pins if p[2] == s] for s in "LRTB"}
    rows = max(len(sides["L"]), len(sides["R"]), 1)
    cols = max(len(sides["T"]), len(sides["B"]), 1)
    w = spec.get("width", max(10.16, 2.54 * (cols + 1)))
    w = math.ceil(w / 2.54) * 2.54
    h = max(2.54 * (rows + 1), 5.08)
    h = math.ceil(h / 2.54) * 2.54
    x0, x1, y0, y1 = -w / 2, w / 2, h / 2, -h / 2
    out = [f'  (symbol "{name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)',
           f'    (property "Reference" "{spec.get("ref", "U")}" (at 0 {r2(y0 + 1.27)} 0) (effects (font (size 1.27 1.27))))',
           f'    (property "Value" "{spec["value"]}" (at 0 {r2(y1 - 1.27)} 0) (effects (font (size 1.27 1.27))))',
           f'    (property "Footprint" "{spec["footprint"]}" (at 0 {r2(y1 - 3.81)} 0) (effects (font (size 1.27 1.27)) hide))',
           f'    (property "Datasheet" "{spec.get("datasheet", "~")}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'    (property "ki_keywords" "{spec.get("keywords", "")}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'    (property "ki_description" "{spec.get("descr", "")}" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'    (symbol "{name}_0_1"',
           f'      (rectangle (start {r2(x0)} {r2(y0)}) (end {r2(x1)} {r2(y1)}) (stroke (width 0.254) (type default)) (fill (type background))))',
           f'    (symbol "{name}_1_1"']

    def pin(num, pname, ptype, x, y, ang):
        return (f'      (pin {PIN_TYPES[ptype]} line (at {r2(x)} {r2(y)} {ang}) (length 2.54) '
                f'(name "{pname}" (effects (font (size 1.016 1.016)))) (number "{num}" (effects (font (size 1.016 1.016)))))')
    for i, (num, pname, _, t) in enumerate(sides["L"]):
        out.append(pin(num, pname, t, x0 - 2.54, y0 - 2.54 * (i + 1), 0))
    for i, (num, pname, _, t) in enumerate(sides["R"]):
        out.append(pin(num, pname, t, x1 + 2.54, y0 - 2.54 * (i + 1), 180))
    for i, (num, pname, _, t) in enumerate(sides["T"]):
        out.append(pin(num, pname, t, x0 + 2.54 * (i + 1), y0 + 2.54, 270))
    for i, (num, pname, _, t) in enumerate(sides["B"]):
        out.append(pin(num, pname, t, x0 + 2.54 * (i + 1), y1 - 2.54, 90))
    out.append("    ))")
    return "\n".join(out)


def symbol_library():
    body = "\n".join(make_symbol(n, s) for n, s in D.SYMBOLS.items())
    return f"(kicad_symbol_lib (version 20220914) (generator insect_tag_build)\n{body}\n)\n"


_libcache = {}


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib == LIB:
        tree = parse(open(os.path.join(PRJ, LIB + ".kicad_sym")).read())
    else:
        if lib not in _libcache:
            _libcache[lib] = parse(open(os.path.join(SYMDIR, lib + ".kicad_sym")).read())
        tree = _libcache[lib]
    import copy
    for e in tree:
        if isinstance(e, list) and e and e[0] == "symbol" and e[1] == name:
            s = copy.deepcopy(e)
            # Resolve "extends" (derived symbols) by copying the parent's units
            ext = next((a for a in s if isinstance(a, list) and a and a[0] == "extends"), None)
            if ext is not None:
                parent = next(p for p in tree if isinstance(p, list) and p and p[0] == "symbol" and p[1] == ext[1])
                parent = copy.deepcopy(parent)
                s = [a for a in s if not (isinstance(a, list) and a and a[0] == "extends")]
                for a in parent:
                    if isinstance(a, list) and a and a[0] == "symbol":
                        a[1] = Q(str(a[1]).replace(str(ext[1]), name, 1))
                        s.append(a)
                    elif isinstance(a, list) and a and a[0] in ("pin_names", "pin_numbers") and not any(
                            isinstance(b, list) and b and b[0] == a[0] for b in s):
                        s.insert(2, a)
            s[1] = Q(lib_id)
            return s
    raise KeyError(lib_id)


def sym_pins(symtree):
    pins = {}

    def walk(t):
        for e in t:
            if isinstance(e, list) and e:
                if e[0] == "pin":
                    at = next(a for a in e if isinstance(a, list) and a[0] == "at")
                    num = next(a for a in e if isinstance(a, list) and a[0] == "number")
                    pins[str(num[1])] = (float(at[1]), float(at[2]), float(at[3]))
                elif e[0] == "symbol":
                    walk(e)
    walk(symtree)
    return pins


# ============================================================ schematic
def rot_ccw(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def r2(v):
    return round(v, 4)


def build_schematic():
    root = U()
    pin_net = {}
    for net, pins in D.NETS.items():
        for ref, p in pins:
            pin_net[(ref, p)] = net
    psym = D.POWER_SYMBOLS
    lib_ids = sorted({p["sym"] for p in D.PARTS} | set(psym.values()) | {"power:PWR_FLAG"})
    libsyms = {lid: lib_symbol(lid) for lid in lib_ids}
    items = []
    pwr_count = [0]

    def prop(name, value, x, y, ang=0, hide=False, justify=None):
        eff = "(font (size 1.27 1.27))"
        if justify:
            eff += f" (justify {justify})"
        if hide:
            eff += " hide"
        return f'(property "{name}" "{value}" (at {r2(x)} {r2(y)} {ang}) (effects {eff}))'

    def instance(lib_id, ref, value, X, Y, ang, fields, in_bom=True, dnp=False, power=False,
                 ref_xy=None, val_xy=None, fp="", mirror=None, ref_just="left", val_just="left"):
        su = U()
        pins = sym_pins(libsyms[lib_id])
        mir = f" (mirror {mirror})" if mirror else ""
        s = [f'(symbol (lib_id "{lib_id}") (at {r2(X)} {r2(Y)} {ang}){mir} (unit 1)',
             f'  (in_bom {"yes" if in_bom else "no"}) (on_board yes) (dnp {"yes" if dnp else "no"})',
             f'  (uuid {su})']
        rx, ry = ref_xy if ref_xy else (X + 3.81, Y - 1.27)
        vx, vy = val_xy if val_xy else (X + 3.81, Y + 1.27)
        s.append("  " + prop("Reference", ref, rx, ry, 0, hide=power, justify=None if power else ref_just))
        s.append("  " + prop("Value", value, vx, vy, 0, justify=None if power else val_just))
        s.append("  " + prop("Footprint", fp, X, Y, 0, hide=True))
        s.append("  " + prop("Datasheet", "~", X, Y, 0, hide=True))
        for k, v in fields.items():
            s.append("  " + prop(k, v, X, Y, 0, hide=True))
        for num in pins:
            s.append(f'  (pin "{num}" (uuid {U()}))')
        s.append(f'  (instances (project "{D.PROJECT}" (path "/{root}" (reference "{ref}") (unit 1))))')
        s.append(")")
        items.append("\n".join(s))
        return su, pins

    def power_symbol(net, x, y, outward):
        pwr_count[0] += 1
        ref = f"#PWR{pwr_count[0]:02d}"
        up = net != "GND"
        if up:
            ang = {90: 0, 270: 180, 180: 90, 0: 270}[outward]
        else:
            ang = {270: 0, 0: 90, 90: 180, 180: 270}[outward]
        instance(psym[net], ref, net, x, y, ang, {}, in_bom=False, power=True,
                 ref_xy=(x, y + (2.54 if up else 5.08)),
                 val_xy=(x + (0 if outward in (90, 270) else (2.54 if outward == 0 else -2.54)),
                         y + (-3.81 if outward == 90 else (3.81 if outward == 270 else 0))))

    def wire(x1, y1, x2, y2):
        items.append(f"(wire (pts (xy {r2(x1)} {r2(y1)}) (xy {r2(x2)} {r2(y2)})) "
                     f"(stroke (width 0) (type default)) (uuid {U()}))")

    def label(net, x, y, outward):
        just = "left bottom" if outward in (0, 90) else "right bottom"
        items.append(f'(label "{net}" (at {r2(x)} {r2(y)} {outward}) (fields_autoplaced) '
                     f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid {U()}))')

    def junction(x, y):
        items.append(f"(junction (at {r2(x)} {r2(y)}) (diameter 0) (color 0 0 0 0) (uuid {U()}))")

    sym_uuid = {}
    nc_set = set(getattr(D, "NO_CONNECT", []))
    for p in D.PARTS:
        gx, gy, ang = p["sch"]
        X, Y = gx * G, gy * G
        fields = dict(p.get("fields", {}))
        mirror = p.get("mirror")
        ro = p.get("ref_at")
        vo = p.get("val_at")
        su, pins = instance(p["sym"], p["ref"], p["value"], X, Y, ang, fields,
                            in_bom=p.get("in_bom", True), dnp=p.get("dnp", False), fp=p["fp"], mirror=mirror,
                            ref_xy=(X + ro[0] * G, Y + ro[1] * G) if ro else None,
                            val_xy=(X + vo[0] * G, Y + vo[1] * G) if vo else None,
                            ref_just=ro[2] if ro else "left", val_just=vo[2] if vo else "left")
        sym_uuid[p["ref"]] = su
        side_power = {}
        for num, (px, py, pang) in pins.items():
            net = pin_net.get((p["ref"], num))
            nc = (p["ref"], num) in nc_set
            if net is None and not nc:
                raise SystemExit(f"unconnected pin {p['ref']}.{num}")
            if mirror == "x":
                py, pang = -py, (-pang) % 360
            rx, ry = rot_ccw(px, py, ang)
            cx, cy = X + rx, Y - ry
            outward = int(round((pang + 180 + ang) % 360))
            if nc:
                items.append(f"(no_connect (at {r2(cx)} {r2(cy)}) (uuid {U()}))")
                continue
            dx, dy = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[outward]
            if net in psym and outward in (0, 180):
                ex, ey = cx + dx * 5.08, cy
                wire(cx, cy, ex, ey)
                side_power.setdefault((net, outward), []).append((ex, ey))
                continue
            ex, ey = cx + dx * 2.54, cy + dy * 2.54
            wire(cx, cy, ex, ey)
            if net in psym:
                power_symbol(net, ex, ey, outward)
            else:
                label(net, ex, ey, outward)
        for (net, outward), ends in side_power.items():
            ends.sort(key=lambda e: e[1])
            x = ends[0][0]
            if len(ends) > 1:
                wire(x, ends[0][1], x, ends[-1][1])
                for e in ends[1:-1]:
                    junction(*e)
            if net != "GND":
                top = ends[0][1]
                wire(x, top, x, top - 2.54)
                if len(ends) > 1:
                    junction(x, top)
                power_symbol(net, x, top - 2.54, 90)
            else:
                bot = ends[-1][1]
                wire(x, bot, x, bot + 2.54)
                if len(ends) > 1:
                    junction(x, bot)
                power_symbol(net, x, bot + 2.54, 270)

    for i, net in enumerate(D.FLAG_NETS):
        x, y = (D.FLAG_AT[0] + 8 * i) * G, D.FLAG_AT[1] * G
        instance("power:PWR_FLAG", f"#FLG0{i + 1}", "PWR_FLAG", x, y, 0, {}, in_bom=False, power=True,
                 ref_xy=(x, y - 1.905), val_xy=(x, y - 3.81))
        wire(x, y, x, y + 2.54)
        power_symbol(net, x, y + 2.54, 270)

    for i, t in enumerate(D.SCH_NOTES):
        items.append(f'(text "{t}" (at {r2(D.NOTES_AT[0] * G)} {r2((D.NOTES_AT[1] + 2.2 * i) * G)} 0) '
                     f'(effects (font (size 1.524 1.524)) (justify left bottom)) (uuid {U()}))')

    lib_block = "(lib_symbols\n" + "\n".join("  " + dump(libsyms[l], 1) for l in lib_ids) + ")"
    sch = (f'(kicad_sch (version 20230121) (generator eeschema)\n'
           f'(uuid {root})\n(paper "{getattr(D, "SCH_PAPER", "A4")}")\n'
           f'(title_block (title "{D.TITLE}") (date "2026-11-02") (rev "{D.REV}")\n'
           f'  (comment 1 "Open hardware, CERN-OHL-S-2.0. (C) 2026 Pavan Kumar Kaushik. Derived from insect_tag_v7")\n'
           f'  (comment 2 "{D.SCH_COMMENT}"))\n'
           f'{lib_block}\n' + "\n".join(items) +
           '\n(sheet_instances (path "/" (page "1")))\n)\n')
    with open(os.path.join(PRJ, D.PROJECT + ".kicad_sch"), "w") as f:
        f.write(sch)
    return root, sym_uuid


# ============================================================ board
def build_board(root_uuid, sym_uuid):
    import pcbnew
    from pcbnew import FromMM, VECTOR2I

    X0, Y0 = 100.0, 100.0

    def P(x, y):
        return VECTOR2I(FromMM(X0 + x), FromMM(Y0 + y))

    path = os.path.join(PRJ, D.PROJECT + ".kicad_pcb")
    board = pcbnew.NewBoard(path)
    board.SetCopperLayerCount(2)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(FromMM(D.BOARD_THICKNESS))

    psym = D.POWER_SYMBOLS
    nets = {}
    for n in D.NETS:
        ni = pcbnew.NETINFO_ITEM(board, n if n in psym else "/" + n)
        board.Add(ni)
        nets[n] = ni
    pin_net = {(r, p): n for n, pins in D.NETS.items() for r, p in pins}
    pin_names = {}
    for sname, spec in D.SYMBOLS.items():
        for num, pname, _, _ in spec["pins"]:
            pin_names[(sname, num)] = pname
    for ref, num in getattr(D, "NO_CONNECT", []):
        part = next(p for p in D.PARTS if p["ref"] == ref)
        sname = part["sym"].split(":")[1]
        pname = pin_names.get((sname, num), num)
        n = f"unconnected-({ref}-{pname}-Pad{num})"
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        nets[n] = ni
        pin_net[(ref, num)] = n

    def load(fpid):
        lib, name = fpid.split(":")
        libpath = os.path.join(PRJ, LIB + ".pretty") if lib == LIB else os.path.join(FPDIR, lib + ".pretty")
        fp = pcbnew.FootprintLoad(libpath, name)
        if fp is None:
            raise SystemExit("cannot load " + fpid)
        return fp

    fps = {}
    for p in D.PARTS + D.BOARD_ONLY:
        fp = load(p["fp"])
        x, y, rot, side = p["pcb"]
        fp.SetReference(p["ref"])
        fp.SetValue(p.get("value", p["fp"].split(":")[1]))
        fp.SetPosition(P(x, y))
        fp.SetOrientationDegrees(rot)
        board.Add(fp)
        if side == "B":
            fp.Flip(P(x, y), True)
        if p["ref"] in sym_uuid:
            fp.SetPath(pcbnew.KIID_PATH(f"/{sym_uuid[p['ref']]}"))
        fp.Reference().SetLayer(pcbnew.B_Fab if side == "B" else pcbnew.F_Fab)
        fp.Reference().SetTextSize(VECTOR2I(FromMM(0.5), FromMM(0.5)))
        fp.Reference().SetTextThickness(FromMM(0.08))
        fp.Value().SetVisible(False)
        for k, v in p.get("fields", {}).items():
            fp.SetProperty(k, v)
        if p.get("dnp") or not p.get("in_bom", True):
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_BOM)
        if p.get("dnp"):
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        for pad in fp.Pads():
            n = pin_net.get((p["ref"], pad.GetNumber()))
            if n:
                pad.SetNet(nets[n])
        fps[p["ref"]] = fp

    def padpos(ref, num):
        for pad in fps[ref].Pads():
            if pad.GetNumber() == num:
                v = pad.GetPosition()
                return pcbnew.ToMM(v.x) - X0, pcbnew.ToMM(v.y) - Y0
        raise KeyError((ref, num))

    for net, layer, width, pts in D.static_tracks():
        xy = [padpos(*q) if isinstance(q[0], str) else q for q in pts]
        for (x1, y1), (x2, y2) in zip(xy, xy[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(P(x1, y1))
            t.SetEnd(P(x2, y2))
            t.SetWidth(FromMM(width))
            t.SetLayer(pcbnew.F_Cu if layer == "F" else pcbnew.B_Cu)
            t.SetNet(nets[net])
            board.Add(t)
    for v_ in D.static_vias():
        net, x, y = v_[:3]
        d, drill = (v_[3], v_[4]) if len(v_) > 3 else (D.VIA_D, D.VIA_DRILL)
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(P(x, y))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(FromMM(d))
        v.SetDrill(FromMM(drill))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(nets[net])
        board.Add(v)

    def seg(a, b, layer=pcbnew.Edge_Cuts, w=0.05):
        sh = pcbnew.PCB_SHAPE(board)
        sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
        sh.SetStart(P(*a))
        sh.SetEnd(P(*b))
        sh.SetLayer(layer)
        sh.SetWidth(FromMM(w))
        board.Add(sh)

    poly = D.outline_polygon().simplify(0.002)
    pts = list(poly.exterior.coords)
    for a, b in zip(pts, pts[1:]):
        seg(a, b)
    for hole in getattr(D, "NPTH", []):   # (x, y, d)
        pass

    def zone_poly(layer, netname, pts, keepout=None, priority=0, clearance=None):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        if keepout:
            z.SetIsRuleArea(True)
            z.SetDoNotAllowCopperPour("pour" in keepout)
            z.SetDoNotAllowTracks("tracks" in keepout)
            z.SetDoNotAllowVias("vias" in keepout)
            z.SetDoNotAllowPads(False)
            z.SetDoNotAllowFootprints(False)
        else:
            z.SetNet(nets[netname])
            z.SetLocalClearance(FromMM(clearance if clearance is not None else D.ZONE_CLEARANCE))
            z.SetMinThickness(FromMM(0.12))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
            z.SetThermalReliefGap(FromMM(0.2))
            z.SetThermalReliefSpokeWidth(FromMM(0.25))
            z.SetAssignedPriority(priority)
            z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            ol.Append(FromMM(X0 + x), FromMM(Y0 + y))
        board.Add(z)
        return z

    LAY = {"F": pcbnew.F_Cu, "B": pcbnew.B_Cu}
    for zd in D.ZONES:
        zone_poly(LAY[zd["layer"]], zd["net"], zd["pts"], priority=zd.get("priority", 0), clearance=zd.get("clearance"))
    for kd in getattr(D, "KEEPOUTS", []):
        zone_poly(LAY[kd["layer"]], None, kd["pts"], keepout=kd["what"])

    def silk(text, x, y, size=0.6, layer=pcbnew.F_SilkS, mirror=False, angle=0, thick=0.12):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(P(x, y))
        t.SetLayer(layer)
        t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size)))
        t.SetTextThickness(FromMM(thick))
        if angle:
            t.SetTextAngleDegrees(angle)
        if mirror:
            t.SetMirrored(True)
        board.Add(t)

    for st in D.SILK_TEXT:
        text, x, y, size, side, angle = st[:6]
        thick = st[6] if len(st) > 6 else min(0.12, size * 0.18)
        silk(text, x, y, size, pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS, side == "B", angle, thick)
    for (x1, y1), (x2, y2), side in D.SILK_LINES:
        seg((x1, y1), (x2, y2), pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS, 0.1)
    for x1, y1, x2, y2, layer in getattr(D, "FAB_LINES", []):
        seg((x1, y1), (x2, y2), getattr(pcbnew, layer), 0.05)

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(path, board)
    fix_fpids(path)
    return board


def fix_fpids(path):
    """Write 'Library:Footprint' ids into the saved board (the SWIG LIB_ID setters fail on this build)."""
    want = {p["ref"]: p["fp"] for p in D.PARTS + D.BOARD_ONLY}
    txt = open(path).read()
    out, pos = [], 0
    for m in re.finditer(r'\(footprint "([^"]+)"', txt):
        start = m.start()
        nxt = txt.find('(footprint "', m.end())
        block = txt[start: nxt if nxt != -1 else len(txt)]
        r = re.search(r'\(fp_text reference "([^"]+)"', block)
        ref = r.group(1) if r else None
        out.append(txt[pos:start])
        out.append(f'(footprint "{want[ref]}"' if ref in want else m.group(0))
        pos = m.end()
    out.append(txt[pos:])
    open(path, "w").write("".join(out))


# ============================================================ project rules
def patch_project():
    pro = os.path.join(PRJ, D.PROJECT + ".kicad_pro")
    d = json.load(open(pro))
    rules = d["board"]["design_settings"]["rules"]
    rules.update({
        "min_clearance": 0.127, "min_track_width": 0.127, "min_via_diameter": 0.3,
        "min_through_hole_diameter": 0.15, "min_via_annular_width": 0.075,
        "min_copper_edge_clearance": 0.2, "min_hole_clearance": 0.2, "min_hole_to_hole": 0.25,
        "min_silk_clearance": 0.0, "min_text_height": 0.5, "min_text_thickness": 0.08,
    })
    sev = d["board"]["design_settings"].setdefault("rule_severities", {})
    for k in ("silk_over_copper", "silk_overlap", "silk_edge_clearance", "text_height", "text_thickness",
              "footprint_type_mismatch", "lib_footprint_issues", "lib_footprint_mismatch"):
        sev[k] = "ignore"
    sev["courtyards_overlap"] = "warning"
    nc = d["net_settings"]["classes"][0]
    nc.update({"clearance": 0.13, "track_width": 0.13, "via_diameter": D.VIA_D, "via_drill": D.VIA_DRILL})
    d["board"]["design_settings"]["track_widths"] = [0.0, 0.13, 0.15, 0.2, 0.25, 0.3]
    d["board"]["design_settings"]["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0},
                                                       {"diameter": D.VIA_D, "drill": D.VIA_DRILL}]
    json.dump(d, open(pro, "w"), indent=2)


def refill():
    """Refill the pours with the project's rules (edge clearance etc.), which only exist once patch_project ran."""
    import pcbnew
    path = os.path.join(PRJ, D.PROJECT + ".kicad_pcb")
    board = pcbnew.LoadBoard(path)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pcbnew.SaveBoard(path, board)
    fix_fpids(path)


def write_tables():
    open(os.path.join(PRJ, LIB + ".kicad_sym"), "w").write(symbol_library())
    open(os.path.join(PRJ, "sym-lib-table"), "w").write(
        f'(sym_lib_table\n  (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.kicad_sym")(options "")(descr "tag symbols"))\n)\n')
    open(os.path.join(PRJ, "fp-lib-table"), "w").write(
        f'(fp_lib_table\n  (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.pretty")(options "")(descr "tag footprints"))\n)\n')


if __name__ == "__main__":
    write_tables()
    root, su = build_schematic()
    build_board(root, su)
    patch_project()
    refill()
    print("built", PRJ)
