"""Build the insect tag KiCad project (schematic, symbol lib, board, project rules) from design.py.

Run with KiCad's Python:  /usr/bin/python3 tools/build.py
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
SYMDIR = "/usr/share/kicad/symbols"
FPDIR = "/usr/share/kicad/footprints"
G = 1.27  # schematic grid


def U():
    return str(uuid.uuid4())


# ============================================================ S-expressions
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
        head = []
        rest = []
        for e in x:
            (rest if (isinstance(e, list) or rest) else head).append(e)
        s = "(" + " ".join(dump(e) for e in head)
        for e in rest:
            s += "\n" + "  " * (ind + 1) + dump(e, ind + 1)
        return s + ")"
    if isinstance(x, Q):
        return '"' + x + '"'
    return str(x)


_libcache = {}


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib == "insect_tag":
        tree = parse(open(os.path.join(PRJ, "insect_tag.kicad_sym")).read())
    else:
        if lib not in _libcache:
            _libcache[lib] = parse(open(os.path.join(SYMDIR, lib + ".kicad_sym")).read())
        tree = _libcache[lib]
    for e in tree:
        if isinstance(e, list) and e and e[0] == "symbol" and e[1] == name:
            import copy
            s = copy.deepcopy(e)
            s[1] = Q(lib_id)
            return s
    raise KeyError(lib_id)


def sym_pins(symtree):
    """Return {number: (x, y, angle)} from a library symbol tree (unit 1 / common)."""
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


# ============================================================ custom symbol
IN100_SYM = """(kicad_symbol_lib (version 20220914) (generator insect_tag_build)
  (symbol "IN100_QFN18" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)
    (property "Reference" "U" (at 0 12.7 0) (effects (font (size 1.27 1.27))))
    (property "Value" "IN100-Q1-R-RC1I" (at 0 -22.86 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "insect_tag:InPlay_IN100_QFN-18-1EP_3x3mm_P0.4mm_EP1.5x1.7mm" (at 0 -25.4 0) (effects (font (size 1.27 1.27)) hide))
    (property "Datasheet" "https://www.inplay-tech.com/in100" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "ki_keywords" "BLE beacon NanoBeacon InPlay" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (property "ki_description" "InPlay IN100 NanoBeacon BLE beacon SoC, QFN18 3x3mm, 1.1-3.6V" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))
    (symbol "IN100_QFN18_0_1"
      (rectangle (start -13.97 10.16) (end 13.97 -17.78) (stroke (width 0.254) (type default)) (fill (type background))))
    (symbol "IN100_QFN18_1_1"
      (pin input line (at -16.51 7.62 0) (length 2.54) (name "CHIP_EN" (effects (font (size 1.27 1.27)))) (number "18" (effects (font (size 1.27 1.27)))))
      (pin passive line (at -16.51 5.08 0) (length 2.54) (name "XO_N" (effects (font (size 1.27 1.27)))) (number "1" (effects (font (size 1.27 1.27)))))
      (pin passive line (at -16.51 2.54 0) (length 2.54) (name "XO_P" (effects (font (size 1.27 1.27)))) (number "2" (effects (font (size 1.27 1.27)))))
      (pin bidirectional line (at -16.51 0.00 0) (length 2.54) (name "GPIO0/RXD" (effects (font (size 1.27 1.27)))) (number "8" (effects (font (size 1.27 1.27)))))
      (pin bidirectional line (at -16.51 -2.54 0) (length 2.54) (name "GPIO1/TXD" (effects (font (size 1.27 1.27)))) (number "9" (effects (font (size 1.27 1.27)))))
      (pin bidirectional line (at -16.51 -5.08 0) (length 2.54) (name "MGPIO4" (effects (font (size 1.27 1.27)))) (number "12" (effects (font (size 1.27 1.27)))))
      (pin bidirectional line (at -16.51 -7.62 0) (length 2.54) (name "MGPIO5" (effects (font (size 1.27 1.27)))) (number "5" (effects (font (size 1.27 1.27)))))
      (pin bidirectional line (at -16.51 -10.16 0) (length 2.54) (name "MGPIO6" (effects (font (size 1.27 1.27)))) (number "4" (effects (font (size 1.27 1.27)))))
      (pin bidirectional line (at -16.51 -12.70 0) (length 2.54) (name "MGPIO7" (effects (font (size 1.27 1.27)))) (number "3" (effects (font (size 1.27 1.27)))))
      (pin power_in line (at 16.51 7.62 180) (length 2.54) (name "VCC" (effects (font (size 1.27 1.27)))) (number "17" (effects (font (size 1.27 1.27)))))
      (pin power_in line (at 16.51 5.08 180) (length 2.54) (name "VDDQ" (effects (font (size 1.27 1.27)))) (number "13" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 16.51 2.54 180) (length 2.54) (name "RF_TX" (effects (font (size 1.27 1.27)))) (number "16" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 16.51 0.00 180) (length 2.54) (name "RTC_XO_P" (effects (font (size 1.27 1.27)))) (number "14" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 16.51 -2.54 180) (length 2.54) (name "RTC_XO_N" (effects (font (size 1.27 1.27)))) (number "15" (effects (font (size 1.27 1.27)))))
      (pin bidirectional line (at 16.51 -5.08 180) (length 2.54) (name "GPIO2" (effects (font (size 1.27 1.27)))) (number "10" (effects (font (size 1.27 1.27)))))
      (pin bidirectional line (at 16.51 -7.62 180) (length 2.54) (name "GPIO3" (effects (font (size 1.27 1.27)))) (number "11" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 16.51 -10.16 180) (length 2.54) (name "SW0" (effects (font (size 1.27 1.27)))) (number "6" (effects (font (size 1.27 1.27)))))
      (pin passive line (at 16.51 -12.70 180) (length 2.54) (name "SW1" (effects (font (size 1.27 1.27)))) (number "7" (effects (font (size 1.27 1.27)))))
      (pin power_in line (at 0 -20.32 90) (length 2.54) (name "GND/EP" (effects (font (size 1.27 1.27)))) (number "19" (effects (font (size 1.27 1.27))))))))
"""


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

    lib_ids = sorted({p["sym"] for p in D.PARTS} | {"power:VCC", "power:GND", "power:PWR_FLAG"})
    libsyms = {lid: lib_symbol(lid) for lid in lib_ids}

    items = []   # schematic items (strings)
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
        if net == "VCC":
            ang = {90: 0, 270: 180, 180: 90, 0: 270}[outward]
        else:
            ang = {270: 0, 0: 90, 90: 180, 180: 270}[outward]
        instance(f"power:{net}", ref, net, x, y, ang, {}, in_bom=False, power=True,
                 ref_xy=(x, y + (2.54 if net == "VCC" else 5.08)),
                 val_xy=(x + (0 if outward in (90, 270) else (2.54 if outward == 0 else -2.54)),
                         y + (-3.81 if outward == 90 else (3.81 if outward == 270 else 0))))

    def wire(x1, y1, x2, y2):
        items.append(f"(wire (pts (xy {r2(x1)} {r2(y1)}) (xy {r2(x2)} {r2(y2)})) "
                     f"(stroke (width 0) (type default)) (uuid {U()}))")

    def label(net, x, y, outward):
        ang = {0: 0, 90: 90, 180: 180, 270: 270}[outward]
        just = "left bottom" if outward in (0, 90) else "right bottom"
        items.append(f'(label "{net}" (at {r2(x)} {r2(y)} {ang}) (fields_autoplaced) '
                     f'(effects (font (size 1.27 1.27)) (justify {just})) (uuid {U()}))')

    def junction(x, y):
        items.append(f"(junction (at {r2(x)} {r2(y)}) (diameter 0) (color 0 0 0 0) (uuid {U()}))")

    sym_uuid = {}
    for p in D.PARTS:
        gx, gy, ang = p["sch"]
        X, Y = gx * G, gy * G
        fields = dict(p["fields"])
        mirror = p.get("mirror")
        ro = p.get("ref_at")   # (dx, dy, justify) in grid units relative to the symbol origin
        vo = p.get("val_at")
        su, pins = instance(p["sym"], p["ref"], p["value"], X, Y, ang, fields,
                            in_bom=p.get("in_bom", True), dnp=p.get("dnp", False), fp=p["fp"],
                            mirror=mirror,
                            ref_xy=(X + ro[0] * G, Y + ro[1] * G) if ro else None,
                            val_xy=(X + vo[0] * G, Y + vo[1] * G) if vo else None,
                            ref_just=ro[2] if ro else "left", val_just=vo[2] if vo else "left")
        sym_uuid[p["ref"]] = su
        side_power = {}   # (net, outward) -> list of stub ends, for power pins leaving sideways
        for num, (px, py, pang) in pins.items():
            net = pin_net.get((p["ref"], num))
            nc = (p["ref"], num) in set(getattr(D, "NO_CONNECT", []))
            if net is None and not nc:
                raise SystemExit(f"unconnected pin {p['ref']}.{num}")
            if mirror == "x":
                py, pang = -py, (-pang) % 360
            rx, ry = rot_ccw(px, py, ang)
            cx, cy = X + rx, Y - ry                     # connection point (screen coords)
            outward = int(round((pang + 180 + ang) % 360))
            if nc:
                items.append(f"(no_connect (at {r2(cx)} {r2(cy)}) (uuid {U()}))")
                continue
            dx, dy = {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[outward]
            if net in D.POWER_NETS and outward in (0, 180):
                ex, ey = cx + dx * 5.08, cy
                wire(cx, cy, ex, ey)
                side_power.setdefault((net, outward), []).append((ex, ey))
                continue
            ex, ey = cx + dx * 2.54, cy + dy * 2.54
            wire(cx, cy, ex, ey)
            if net in D.POWER_NETS:
                power_symbol(net, ex, ey, outward)
            else:
                label(net, ex, ey, outward)
        # Sideways power pins: join their stub ends with one vertical wire, then one power symbol
        # above (VCC) or below (GND).
        for (net, outward), ends in side_power.items():
            ends.sort(key=lambda e: e[1])
            x = ends[0][0]
            if len(ends) > 1:
                wire(x, ends[0][1], x, ends[-1][1])
                for e in ends[1:-1]:
                    junction(*e)
            if net == "VCC":
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

    # Power flags so ERC knows VCC and GND are driven (the battery is passive).
    for i, net in enumerate(["VCC", "GND"]):
        x, y = (D.FLAG_AT[0] + 8 * i) * G, D.FLAG_AT[1] * G
        instance("power:PWR_FLAG", f"#FLG0{i + 1}", "PWR_FLAG", x, y, 0, {}, in_bom=False, power=True,
                 ref_xy=(x, y - 1.905), val_xy=(x, y - 3.81))
        wire(x, y, x, y + 2.54)
        power_symbol(net, x, y + 2.54, 270)

    notes = [
        "IN100 insect tag v5: 8 mm round tag, wire antenna, cut-off programming tab",
        "- U1 IN100 QFN18 (JLC C6062024). CHIP_EN, VDDQ and VCC tied together; unused GPIOs, switches and RTC pins left open.",
        "- Supply 3.3 V on the tab pads while burning the OTP; never with the cell fitted.",
        "- Y1 26 MHz 1612, 7 pF load: the IN100's on-chip load capacitance replaces external caps.",
        "- C1 100 nF at VCC. C2 100 uF 0805: the 337 cell (~80 ohm) cannot supply 9-14 mA TX bursts alone.",
        "- AE1: ~30 mm enamelled wire in a plated hole, fed straight from RF_TX (trim to tune).",
        "- BT1: 337 / SR416SW cell under the tag: - cap silver-epoxied to the underside pad, + wire to the top rim pad.",
        "- J1: 2 x 2 plated pads on the tab (R T / + G); cut the neck after programming.",
        "Derived from the IN100 datasheet reference design and SparkFun's NanoBeacon Lite board (CC BY-SA 4.0).",
    ]
    for i, t in enumerate(notes):
        items.append(f'(text "{t}" (at {r2(20 * G)} {r2((132 + 2.2 * i) * G)} 0) '
                     f'(effects (font (size 1.524 1.524)) (justify left bottom)) (uuid {U()}))')

    lib_block = "(lib_symbols\n" + "\n".join("  " + dump(libsyms[l], 1) for l in lib_ids) + ")"
    sch = (f'(kicad_sch (version 20230121) (generator eeschema)\n'
           f'(uuid {root})\n(paper "A4")\n'
           f'(title_block (title "IN100 insect tracking tag v5") (date "2026-10-30") (rev "E")\n'
           f'  (comment 1 "Open hardware. Hubble or Apple Find My, chosen when the IN100 is programmed")\n'
           f'  (comment 2 "Derived from the InPlay IN100 reference design and SparkFun NanoBeacon (CC BY-SA 4.0)"))\n'
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
    ds.SetBoardThickness(FromMM(0.6))

    nets = {}
    for n in D.NETS:
        # Power nets take the power symbol's global name; the others come from local labels, which KiCad names "/NET".
        ni = pcbnew.NETINFO_ITEM(board, n if n in D.POWER_NETS else "/" + n)
        board.Add(ni)
        nets[n] = ni

    pin_net = {(r, p): n for n, pins in D.NETS.items() for r, p in pins}
    # Unused pins: KiCad names their nets "unconnected-(REF-PIN-PadN)"; give the pads the same names for parity.
    pin_names = dict((num, name) for name, num in re.findall(r'\(name "([^"]+)".*?\(number "([^"]+)"', IN100_SYM))
    for ref, num in getattr(D, "NO_CONNECT", []):
        n = f"unconnected-({ref}-{pin_names[num]}-Pad{num})"
        ni = pcbnew.NETINFO_ITEM(board, n)
        board.Add(ni)
        nets[n] = ni
        pin_net[(ref, num)] = n

    def load(fpid):
        lib, name = fpid.split(":")
        libpath = os.path.join(PRJ, "insect_tag.pretty") if lib == "insect_tag" else os.path.join(FPDIR, lib + ".pretty")
        fp = pcbnew.FootprintLoad(libpath, name)
        if fp is None:
            raise SystemExit("cannot load " + fpid)
        return fp  # library nickname is written into the file afterwards (fix_fpids)

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
        # Keep reference text off the tiny tag's silkscreen (Fab layer only).
        fp.Reference().SetLayer(pcbnew.B_Fab if side == "B" else pcbnew.F_Fab)
        fp.Reference().SetTextSize(VECTOR2I(FromMM(0.5), FromMM(0.5)))
        fp.Reference().SetTextThickness(FromMM(0.08))
        fp.Value().SetVisible(False)
        for k, v in p.get("fields", {}).items():   # carry the symbol fields onto the footprint (KiCad 8+ checks this)
            fp.SetProperty(k, v)
        if p.get("dnp"):
            fp.SetAttributes(fp.GetAttributes() | pcbnew.FP_EXCLUDE_FROM_POS_FILES | pcbnew.FP_EXCLUDE_FROM_BOM)
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

    # Tracks: static ones from design.py (neck, tab, arm) plus the routed ones from routes.json
    routed = {"tracks": [], "vias": []}
    rpath = os.path.join(PRJ, "routes.json")
    if os.path.exists(rpath) and not os.environ.get("NO_ROUTES"):
        routed = json.load(open(rpath))
    for net, layer, width, pts in list(D.static_tracks()) + [tuple(t) for t in routed["tracks"]]:
        xy = [padpos(*q) if isinstance(q[0], str) else q for q in pts]
        for (x1, y1), (x2, y2) in zip(xy, xy[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(P(x1, y1))
            t.SetEnd(P(x2, y2))
            t.SetWidth(FromMM(width))
            t.SetLayer(pcbnew.F_Cu if layer == "F" else pcbnew.B_Cu)
            t.SetNet(nets[net])
            board.Add(t)
    for net, x, y in list(D.static_vias()) + [tuple(v) for v in routed["vias"]]:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(P(x, y))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetWidth(FromMM(D.VIA_D))
        v.SetDrill(FromMM(D.VIA_DRILL))
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(nets[net])
        board.Add(v)

    # Outline: one closed contour from design.outline_polygon() (tag circle, ears, arm, neck, tab).
    def seg(a, b):
        sh = pcbnew.PCB_SHAPE(board)
        sh.SetShape(pcbnew.SHAPE_T_SEGMENT)
        sh.SetStart(P(*a))
        sh.SetEnd(P(*b))
        sh.SetLayer(pcbnew.Edge_Cuts)
        sh.SetWidth(FromMM(0.05))
        board.Add(sh)

    poly = D.outline_polygon().simplify(0.002)
    pts = list(poly.exterior.coords)
    for a, b in zip(pts, pts[1:]):
        seg(a, b)

    # GND pours on both layers, limited to the tag (not the neck or tab).
    def zone_poly(layer, netname, pts, keepout=False):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        if keepout:
            z.SetIsRuleArea(True)
            z.SetDoNotAllowCopperPour(True)
            z.SetDoNotAllowTracks(False)
            z.SetDoNotAllowVias(False)
            z.SetDoNotAllowPads(False)
            z.SetDoNotAllowFootprints(False)
        else:
            z.SetNet(nets[netname])
            z.SetLocalClearance(FromMM(D.ZONE_CLEARANCE))
            z.SetMinThickness(FromMM(0.12))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
            z.SetThermalReliefGap(FromMM(0.2))
            z.SetThermalReliefSpokeWidth(FromMM(0.25))
        ol = z.Outline()
        ol.NewOutline()
        for x, y in pts:
            ol.Append(FromMM(X0 + x), FromMM(Y0 + y))
        board.Add(z)
        return z

    # Pour starts 0.3 mm below the top edge so a panel refill cannot run copper into the top tab's mouse bites.
    tag_poly = [tuple(p) for p in D.pour_polygon().exterior.coords][:-1]
    zone_poly(pcbnew.F_Cu, "GND", tag_poly)
    zone_poly(pcbnew.B_Cu, "GND", tag_poly)

    def silk(text, x, y, size=0.6, layer=pcbnew.F_SilkS, mirror=False, angle=0):
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(P(x, y))
        t.SetLayer(layer)
        t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size)))
        t.SetTextThickness(FromMM(0.12))
        if angle:
            t.SetTextAngleDegrees(angle)
        if mirror:
            t.SetMirrored(True)
        board.Add(t)

    for text, x, y, size, side, angle in D.SILK_TEXT:
        silk(text, x, y, size, pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS, side == "B", angle)
    for (x1, y1), (x2, y2), side in D.SILK_LINES:
        ln = pcbnew.PCB_SHAPE(board)
        ln.SetShape(pcbnew.SHAPE_T_SEGMENT)
        ln.SetStart(P(x1, y1))
        ln.SetEnd(P(x2, y2))
        ln.SetLayer(pcbnew.F_SilkS if side == "F" else pcbnew.B_SilkS)
        ln.SetWidth(FromMM(0.1))
        board.Add(ln)

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
        if ref in want:
            out.append(f'(footprint "{want[ref]}"')
        else:
            out.append(m.group(0))
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
        "min_silk_clearance": 0.0, "min_text_height": 0.6, "min_text_thickness": 0.1,
    })
    sev = d["board"]["design_settings"].setdefault("rule_severities", {})
    # Tiny board: silkscreen-over-copper and text-height checks are informational here.
    for k in ("silk_over_copper", "silk_overlap", "silk_edge_clearance", "text_height", "text_thickness",
              "footprint_type_mismatch", "lib_footprint_issues", "lib_footprint_mismatch"):
        sev[k] = "ignore"
    # Dense 6.4 mm tag: part courtyards touch; copper gaps are checked by the clearance rules.
    sev["courtyards_overlap"] = "warning"
    nc = d["net_settings"]["classes"][0]
    nc.update({"clearance": 0.13, "track_width": 0.13, "via_diameter": D.VIA_D, "via_drill": D.VIA_DRILL})
    d["board"]["design_settings"]["track_widths"] = [0.0, 0.13, 0.15, 0.2, 0.25]
    d["board"]["design_settings"]["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0},
                                                       {"diameter": D.VIA_D, "drill": D.VIA_DRILL}]
    json.dump(d, open(pro, "w"), indent=2)


def write_tables():
    open(os.path.join(PRJ, "insect_tag.kicad_sym"), "w").write(IN100_SYM)
    open(os.path.join(PRJ, "sym-lib-table"), "w").write(
        '(sym_lib_table\n  (version 7)\n  (lib (name "insect_tag")(type "KiCad")(uri "${KIPRJMOD}/insect_tag.kicad_sym")(options "")(descr "IN100 tag symbols"))\n)\n')
    open(os.path.join(PRJ, "fp-lib-table"), "w").write(
        '(fp_lib_table\n  (version 7)\n  (lib (name "insect_tag")(type "KiCad")(uri "${KIPRJMOD}/insect_tag.pretty")(options "")(descr "IN100 tag footprints"))\n)\n')


if __name__ == "__main__":
    write_tables()
    root, su = build_schematic()
    build_board(root, su)
    patch_project()
    print("built", PRJ)
