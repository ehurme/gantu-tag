"""Supply droop during one IN100 advertising event on a silver-oxide cell, v8 D1 (run: python3 tools/burst_sim.py).

Cell = Voc behind R_int; the bulk capacitance (after DC-bias derating) sits across the IN100.
Event model (the IN100 datasheet gives only TX currents, at 3 V): 0.8 ms crystal start at 1.5 mA, then
3 channels x (0.5 ms at TX current incl. PLL ramp + 0.15 ms gap at 3 mA). Same model as v7.

v8.2 capacitors: C1 100 uF 0805 (GRM21BR60J107ME15L) + C4 100 nF (v8.0 also had C3 10 uF 0402; dropped as redundant).
Effective C1 at ~1.5 V: v8.1 assumed ~80 uF. The independent review (F1) found Murata's own model gives 72 uF at 0 V
before DC bias, so with DC bias, -20 % tolerance, cold and ageing: ~55 uF typical, ~45 uF worst case. Both are run.
TX power: the datasheet maximum is +4 dBm (13.8 mA), not +5 dBm.
"""
import numpy as np  # noqa: F401  (kept for parity with v7)

VCC_MIN = 1.1   # IN100 datasheet Table 16 (and 5.2: below 1.1 V it must fall under 0.1 V before restarting)


def profile(i_tx):
    seg = [(0.8e-3, 1.5e-3)]
    for _ in range(3):
        seg += [(0.5e-3, i_tx), (0.15e-3, 3e-3)]
    return seg


def vmin(voc, r, c, i_tx, dt=1e-6, v0=None):
    v = voc if v0 is None else v0
    lo, q = v, 0.0
    for dur, i in profile(i_tx):
        for _ in range(int(round(dur / dt))):
            v += ((voc - v) / r - i) / c * dt
            lo = min(lo, v)
            q += i * dt
    return lo, q


caps = [("v8.1 assumption: 100 uF + 100 nF = 80 uF", 80.1e-6),
        ("v8.0 assumption with C3 10 uF = 88 uF", 88.1e-6),
        ("realistic (review F1): 55 uF", 55.1e-6),
        ("worst case (review F1): 45 uF", 45.1e-6)]
cells = [("fresh, 20 C (80 ohm)", 1.55, 80), ("cold / half used (150 ohm)", 1.53, 150),
         ("end of life (250 ohm)", 1.50, 250), ("cold end of life (400 ohm)", 1.48, 400)]
results = {}
for scale, tag in ((1.0, "datasheet 3 V currents"), (1.5, "TX current x1.5 (if the IN100 draws more at 1.5 V)")):
    print(f"\n==== {tag}")
    for i_tx, name in ((9.1e-3, "0 dBm, 9.1 mA"), (13.8e-3, "+4 dBm (max), 13.8 mA")):
        it = i_tx * scale
        print(f"\nTX {name} x{scale:g}: minimum VCC during one advertising event (IN100 needs >= {VCC_MIN} V)")
        print(f"{'bulk cap':42s}" + "".join(f"{c[0]:>29s}" for c in cells))
        for cname, c in caps:
            row = ""
            for cell_name, voc, r in cells:
                lo, q = vmin(voc, r, c, it)
                results[(scale, name, cname, cell_name)] = lo
                row += f"{lo:>16.2f} V ({lo - VCC_MIN:+5.2f})  "
            print(f"{cname:42s}{row}")

lo, q = vmin(1.55, 80, 55.1e-6, 9.1e-3)
print(f"\ncharge per event at 0 dBm: {q*1e6:.1f} uC")
for cell, cap_mah in (("337 (8.3 mAh)", 8.3), ("364 (23 mAh)", 23), ("377 (27 mAh)", 27)):
    for T in (1, 3, 10):
        i_avg = 0.625e-6 + q / T
        print(f"{cell:14s} interval {T:>3d} s: average {i_avg*1e6:5.2f} uA -> {cap_mah*1e-3/i_avg/24:6.0f} days "
              f"(to empty; ~half that if the last half of a low-drain cell is unusable)")
print()
for r1, var in ((1e6, "V1 (1 Mohm)"), (100e3, "V2 (100 kohm, v8.3)")):
    i_store = 1.55 / r1 + 10e-9
    print(f"OFF bridged, {var}: {i_store*1e6:.2f} uA -> {i_store*24*30*1e3:.3f} mAh per 30 days "
          f"({i_store*24*30/8.3e-3*100:.0f} % of a 337), a 337 lasts {8.3e-3/i_store/24:.0f} days bridged")


def power_up(r_cell, c_bulk, r1, c2, voc=1.55, k_on=0.6, v_por=0.9, dt=1e-6, t_end=0.5):
    """Cell fitted at t = 0 into an empty C1: VCC rises through the cell's resistance, CHIP_EN follows through R1/C2.
    The IN100 starts when CHIP_EN > 0.6 VCC (and VCC > an assumed internal POR); its first advertising event starts
    straight away. Returns (VCC at the start of the event, minimum VCC during it)."""
    v = en = t = 0.0
    while t < t_end:
        v += (voc - v) / r_cell / c_bulk * dt
        en += (v - en) / (r1 * c2) * dt
        t += dt
        if en > k_on * v and v > v_por:
            break
    lo, _ = vmin(voc, r_cell, c_bulk, 9.1e-3, v0=v)
    return v, lo, t


print("\nPower-up race (review F2): cell fitted into an empty C1, 0 dBm first event starting as soon as CHIP_EN > 0.6 VCC")
print(f"{'enable':34s}{'cell':>9s}{'C1':>8s}{'starts at':>12s}{'VCC then':>10s}{'min VCC':>9s}")
for r1, c2, var in ((1e3, 100e-9, "v8.1 V1: 1k / 100 nF (SparkFun)"), (1e6, 100e-9, "v8.2/8.3 V1: 1M / 100 nF"),
                    (1e6, 1e-9, "v8.2 V2: 1M / 1 nF (OFF jumper)"), (100e3, 10e-9, "v8.3 V2: 100k / 10 nF (OFF)")):
    for r_cell in (80, 250):
        for c in (55.1e-6, 45.1e-6):
            v, lo, t = power_up(r_cell, c, r1, c2)
            flag = "  < 1.1 V: brown-out lock" if lo < VCC_MIN else ""
            print(f"{var:34s}{r_cell:>6d} ohm{c*1e6:>6.0f} uF{t*1e3:>9.1f} ms{v:>9.2f} V{lo:>8.2f} V{flag}")
print("(V2 is started by cutting the tail after the cell has been fitted with OFF bridged, so its row only applies if "
      "the cell is fitted with OFF open.)")
print("\nEnable time constants: V1 1M x 100 nF = 100 ms, V2 100k x 10 nF = 1 ms; cell + C1 at power-up: "
      f"80-400 ohm x 45-55 uF = {80*45e-6*1e3:.1f}-{400*55e-6*1e3:.0f} ms")

print("\nCHIP_EN input load (unpublished; v8.3 hedge). CHIP_EN must reach 0.6 VCC through R1:")
print("  a pull-down Rpd needs Rpd >= 1.5 x R1; a constant input current I needs I <= 0.4 VCC / R1 (VCC 1.2-1.55 V)")
for r1, var in ((1e6, "V1, N6 (1 Mohm)"), (100e3, "V2 (100 kohm)"), (1e3, "SparkFun (1 kohm)")):
    print(f"  {var:20s} works with Rpd >= {1.5*r1/1e3:7.1f} kohm, or I <= {0.4*1.2/r1*1e6:7.2f}-{0.4*1.55/r1*1e6:.2f} uA")
